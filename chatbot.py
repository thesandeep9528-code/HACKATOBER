import os
import random
import json
import logging
import re
from pathlib import Path
from functools import lru_cache
from threading import Lock
from flask import Blueprint, request, jsonify

chatbot_bp = Blueprint("chatbot", __name__, template_folder="templates", static_folder="static")
logger = logging.getLogger(__name__)
MAX_TRANSCRIPTION_BYTES = 10 * 1024 * 1024
SUPPORTED_SPEECH_LANGUAGES = {"en", "hi", "te", "ta", "kn", "ml", "bn"}
WHISPER_MODEL_LOCK = Lock()

FAQ_PATH = Path(__file__).resolve().parent / "data" / "chatbot_faqs.json"
with FAQ_PATH.open(encoding="utf-8") as faq_file:
    CHATBOT_FAQS = json.load(faq_file)

if not isinstance(CHATBOT_FAQS, list) or len(CHATBOT_FAQS) > 100:
    raise ValueError("Chatbot FAQ data must be a JSON list containing at most 100 entries.")

FAQ_STOP_WORDS = {
    "a", "an", "and", "are", "can", "do", "does", "for", "how", "i", "in",
    "is", "it", "my", "of", "on", "or", "should", "the", "to", "what",
    "when", "why", "with", "you", "your"
}

OFFLINE_KNOWLEDGE = {
    "wheat": "Wheat thrives in well-drained loamy soil with temperatures between 15°C to 25°C. Critical irrigation stages: Crown Root Initiation (21 DAS) and Flowering.",
    "rice": "Rice requires heavy clay or alluvial soil with high water holding capacity and standing water during vegetative phases. Maintain optimal NPK of 90:50:50.",
    "fertilizer": "Apply nitrogen fertilizers (Urea) in split doses: 50% basal, 25% at tillering, and 25% at panicle/flowering initiation. Phosphatic fertilizers should be applied entirely at sowing.",
    "pest": "For initial pest infestations, apply 5% Neem Oil extract spray. For severe fungal attacks, consider Mancozeb (2g/L) or Copper Oxychloride based on local extension guidelines.",
    "yellow leaves": "Yellowing of older leaves typically indicates Nitrogen (N) deficiency. Interveinal yellowing on younger leaves suggests Iron or Magnesium deficiency.",
    "moisture": "Maintain soil moisture at field capacity (50-70%). Avoid overwatering during ripening/harvest stages to prevent fungal rot."
}

def _faq_tokens(text):
    return {
        token for token in re.findall(r"[a-z0-9]+", text.lower())
        if token not in FAQ_STOP_WORDS and len(token) > 1
    }


def _find_faq(user_question):
    question_tokens = _faq_tokens(user_question)
    if not question_tokens:
        return None

    best_faq = None
    best_score = 0
    for faq in CHATBOT_FAQS:
        keyword_tokens = set()
        for keyword in faq["keywords"]:
            keyword_tokens.update(_faq_tokens(keyword))
        faq_question_tokens = _faq_tokens(faq["question"])
        score = (2 * len(question_tokens & keyword_tokens)) + len(question_tokens & faq_question_tokens)
        if score > best_score:
            best_faq = faq
            best_score = score

    return best_faq if best_score >= 3 else None


@chatbot_bp.route("/chatbot/faqs", methods=["GET"])
def chatbot_faqs():
    return jsonify([
        {
            "category": faq["category"],
            "question": faq["question"]
        }
        for faq in CHATBOT_FAQS
    ])


@chatbot_bp.route("/chatbot/speech-capabilities", methods=["GET"])
def chatbot_speech_capabilities():
    return jsonify({"server_transcription": True, "provider": "local"})


@lru_cache(maxsize=1)
def _get_local_speech_model():
    from faster_whisper import WhisperModel

    model_name = os.getenv("WHISPER_MODEL", "small")
    device = os.getenv("WHISPER_DEVICE", "cpu")
    compute_type = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
    logger.info("Loading local speech model %s on %s.", model_name, device)
    return WhisperModel(model_name, device=device, compute_type=compute_type)


@chatbot_bp.route("/chatbot/transcribe", methods=["POST"])
def transcribe_voice_question():
    if request.content_length and request.content_length > MAX_TRANSCRIPTION_BYTES + 65536:
        return jsonify({"error": "Audio recording is too large. Please record a shorter question."}), 413

    audio = request.files.get("audio")
    if not audio or not audio.filename:
        return jsonify({"error": "No audio recording was received."}), 400
    if not audio.mimetype or not audio.mimetype.startswith("audio/"):
        return jsonify({"error": "Unsupported audio format. Please record again."}), 400

    audio_bytes = audio.stream.read(MAX_TRANSCRIPTION_BYTES + 1)
    if not audio_bytes:
        return jsonify({"error": "The audio recording is empty. Please try again."}), 400
    if len(audio_bytes) > MAX_TRANSCRIPTION_BYTES:
        return jsonify({"error": "Audio recording is too large. Please record a shorter question."}), 413

    language = request.form.get("language", "en").strip().lower()
    if language not in SUPPORTED_SPEECH_LANGUAGES:
        language = "en"

    try:
        from io import BytesIO

        with WHISPER_MODEL_LOCK:
            model = _get_local_speech_model()
            segments, _ = model.transcribe(
                BytesIO(audio_bytes),
                language=language,
                vad_filter=True
            )
            transcript = " ".join(segment.text.strip() for segment in segments).strip()
        if not transcript:
            return jsonify({"error": "No speech was detected. Please try again."}), 422
        return jsonify({"text": transcript, "language": language})
    except Exception:
        logger.exception("Local speech transcription failed.")
        return jsonify({
            "error": "Local speech transcription failed. Check the model download, available memory, audio format, and server logs."
        }), 502


@chatbot_bp.route("/chatbot", methods=["POST"])
def chatbot():
    data = request.get_json() or {}
    user_question = data.get("question", "").strip()

    if not user_question:
        return jsonify({"error": "Question cannot be empty!"}), 400

    matched_faq = _find_faq(user_question)
    if matched_faq:
        return jsonify({
            "response": matched_faq["answer"],
            "source": "faq",
            "category": matched_faq["category"]
        })

    api_key = os.getenv("API_KEY") or os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY")

    if api_key:
        try:
            from openai import OpenAI
            client = OpenAI(
                api_key=api_key,
                base_url=os.getenv("AI_BASE_URL", "https://api.groq.com/openai/v1")
            )

            configured_model = os.getenv("AI_MODEL")
            candidate_models = []
            if configured_model:
                candidate_models.append(configured_model)
            candidate_models.extend(["groq/compound", "groq/compound-mini", "qwen/qwen3.6-27b"])

            bot_reply = None
            for model_name in candidate_models:
                try:
                    completion = client.chat.completions.create(
                        model=model_name,
                        messages=[
                            {
                                "role": "system",
                                "content": "You are BioGrow AI, an expert agricultural consultant. Provide concise, clear, and practical advice for farmers on crops, fertilizers, irrigation, weather adaptation, and pest management."
                            },
                            {"role": "user", "content": user_question}
                        ],
                        max_tokens=450,
                        temperature=0.3
                    )
                    bot_reply = completion.choices[0].message.content
                    if bot_reply:
                        return jsonify({"response": bot_reply})
                except Exception as model_err:
                    # Try next candidate model
                    continue
        except Exception as e:
            # Fall back to knowledge base
            pass

    # Intelligent agronomic knowledge fallback
    q_lower = user_question.lower()
    matched_replies = [val for key, val in OFFLINE_KNOWLEDGE.items() if key in q_lower]

    if matched_replies:
        bot_reply = "🌾 " + " ".join(matched_replies)
    else:
        bot_reply = (
            "🌾 **BioGrow Farming Advisory:** For optimal crop health, monitor soil moisture weekly, "
            "perform balanced N-P-K fertilizer application based on your soil test, and use the **Leaf Doctor** "
            "tool to diagnose any foliar symptoms early. Feel free to ask about specific crops, pests, or fertilizers!"
        )

    return jsonify({"response": bot_reply})

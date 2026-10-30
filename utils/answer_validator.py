import os
import json
import re

def validate_answer_with_ai(question, answer):
    api_key = os.getenv("API_KEY") or os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY")

    # If API key is configured, query the model
    if api_key:
        try:
            from openai import OpenAI
            client = OpenAI(
                api_key=api_key,
                base_url=os.getenv("AI_BASE_URL", "https://api.groq.com/openai/v1")
            )
            prompt = f"""
You are a strict Agricultural Quality Assurance Auditor.
Evaluate if the following user answer provides a helpful, actionable solution to the farmer's question.

Question: {question}
Answer: {answer}

Criteria:
1. Specificity: Mentions concrete recommendations (e.g. fertilizer types, watering, treatments, practices).
2. Actionability: Avoid generic non-answers like "ask an expert" or "don't know".
3. Length: Must be informative.

Return ONLY strict JSON in this format:
{{
  "is_valid": true,
  "confidence": 85,
  "reason": "Clear explanation"
}}
"""
            completion = client.chat.completions.create(
                model=os.getenv("AI_MODEL", "llama-3.1-8b-instant"),
                messages=[
                    {"role": "system", "content": "You are an agricultural expert validating farmer answers."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )
            content = completion.choices[0].message.content.strip()
            # Extract json block if wrapped in markdown
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json_match.group(0)
            return content
        except Exception as e:
            # Fall back to heuristic validation
            pass

    # Heuristic Rule-Based Fallback
    text = answer.strip().lower()
    words = text.split()

    if len(words) < 3:
        return json.dumps({
            "is_valid": False,
            "confidence": 30,
            "reason": "Answer is too short. Please provide actionable details or specific recommendations."
        })

    vague_phrases = ["idk", "don't know", "no idea", "solve it", "yes", "no", "google it"]
    if any(p in text for p in vague_phrases) and len(words) < 8:
        return json.dumps({
            "is_valid": False,
            "confidence": 35,
            "reason": "The answer appears too vague. Please provide specific agricultural techniques or treatments."
        })

    return json.dumps({
        "is_valid": True,
        "confidence": 85,
        "reason": "The answer provides constructive agricultural advice for the community."
    })
import json
import io
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import app


class ChatbotFaqTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        faq_path = Path(__file__).resolve().parents[1] / "data" / "chatbot_faqs.json"
        self.faqs = json.loads(faq_path.read_text(encoding="utf-8"))

    def test_faq_file_contains_100_complete_entries(self):
        self.assertEqual(len(self.faqs), 100)
        for faq in self.faqs:
            with self.subTest(question=faq.get("question")):
                self.assertTrue(faq["category"])
                self.assertTrue(faq["question"])
                self.assertTrue(faq["answer"])
                self.assertTrue(faq["keywords"])

    def test_faq_endpoint_lists_questions_and_categories(self):
        response = self.client.get("/chatbot/faqs")

        self.assertEqual(response.status_code, 200)
        questions = response.get_json()
        self.assertEqual(len(questions), 100)
        self.assertTrue(all(item["question"] and item["category"] for item in questions))

    def test_each_faq_question_returns_its_faq_answer(self):
        for faq in self.faqs:
            with self.subTest(question=faq["question"]):
                response = self.client.post(
                    "/chatbot",
                    json={"question": faq["question"]}
                )

                self.assertEqual(response.status_code, 200)
                result = response.get_json()
                self.assertEqual(result["source"], "faq")
                self.assertEqual(result["response"], faq["answer"])

    def test_empty_question_is_rejected(self):
        response = self.client.post("/chatbot", json={"question": "  "})

        self.assertEqual(response.status_code, 400)

    def test_chatbot_has_voice_input_and_output_controls(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'id="chat-voice-input"', response.data)
        self.assertIn(b'id="chat-voice-output"', response.data)
        self.assertIn(b'id="chat-voice-status"', response.data)

    def test_speech_capabilities_reports_server_transcription_setting(self):
        response = self.client.get("/chatbot/speech-capabilities")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["server_transcription"])
        self.assertEqual(response.get_json()["provider"], "local")

    def test_transcription_works_without_api_keys(self):
        mock_model = Mock()
        mock_model.transcribe.return_value = (
            iter([SimpleNamespace(text="My crop leaves are yellow.")]),
            SimpleNamespace(language="hi")
        )
        with patch("chatbot._get_local_speech_model", return_value=mock_model):
            response = self.client.post(
                "/chatbot/transcribe",
                data={
                    "language": "hi",
                    "audio": (io.BytesIO(b"sample audio"), "question.webm", "audio/webm")
                },
                content_type="multipart/form-data"
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {
            "text": "My crop leaves are yellow.",
            "language": "hi"
        })
        mock_model.transcribe.assert_called_once()
        self.assertEqual(mock_model.transcribe.call_args.kwargs["language"], "hi")

    def test_transcription_failure_is_reported(self):
        with patch("chatbot._get_local_speech_model", side_effect=RuntimeError("Model unavailable")):
            response = self.client.post(
                "/chatbot/transcribe",
                data={"audio": (io.BytesIO(b"sample audio"), "question.webm", "audio/webm")},
                content_type="multipart/form-data"
            )

        self.assertEqual(response.status_code, 502)
        self.assertIn("Local speech transcription failed", response.get_json()["error"])


if __name__ == "__main__":
    unittest.main()

import io

from fastapi.testclient import TestClient
from PyPDF2 import PdfWriter

from app.config import Settings
from app.main import app
from app.routes import api
from app.services.gemini import GeminiService


client = TestClient(app)


def make_blank_pdf() -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


class FakeGemini:
    def generate_text(self, prompt: str, temperature: float = 0.4) -> str:
        return "Mock educational answer."

    def quiz_from_text(self, topic: str, language: str, source: str):
        return {
            "quiz": [
                {
                    "question": "Which option is correct?",
                    "options": {"A": "Correct", "B": "Wrong", "C": "Wrong", "D": "Wrong"},
                    "correct": "A",
                    "explanation": "A is correct in this test.",
                }
            ],
            "topic": topic,
        }

    def learning_path(self, topic, level, goal, hours, language):
        return {
            "topic": topic,
            "level": level,
            "goal": goal,
            "weeks": [
                {
                    "week": 1,
                    "title": "Foundations",
                    "objectives": ["Understand the basics"],
                    "activities": ["Read and practice"],
                    "checkpoint": "Complete a short exercise",
                }
            ],
        }


def setup_function():
    api.gemini = FakeGemini()


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_index():
    response = client.get("/")
    assert response.status_code == 200
    assert "EduGenie" in response.text


def test_ask_validation():
    response = client.post("/api/ask", json={"question": "Explain AI", "language": "English"})
    assert response.status_code == 200
    assert response.json()["answer"] == "Mock educational answer."


def test_ask_rejects_empty_question():
    response = client.post("/api/ask", json={"question": "", "language": "English"})
    assert response.status_code == 422


def test_quiz_requires_topic_or_file():
    response = client.post("/api/quiz", data={"topic": "", "language": "English"})
    assert response.status_code == 400


def test_learning_path():
    response = client.post(
        "/api/learning-path",
        json={
            "topic": "Python",
            "current_level": "Beginner",
            "goal": "Build web apps",
            "hours_per_week": 5,
            "language": "English",
        },
    )
    assert response.status_code == 200
    assert response.json()["weeks"][0]["week"] == 1


def test_unsupported_language_is_rejected():
    response = client.post("/api/ask", json={"question": "Explain AI", "language": "French"})
    assert response.status_code == 422


def test_missing_gemini_key_returns_service_error():
    settings = Settings(gemini_api_key="", gemini_model="gemini-2.5-flash")
    service = GeminiService(settings)
    assert service.client is None
    try:
        service.generate_text("hello")
    except Exception as exc:
        assert "not configured" in str(exc).lower()


def test_generate_structured_accepts_markdown_json():
    service = GeminiService(Settings(gemini_api_key="token"))

    class FakeResponse:
        text = "```json\n{\"quiz\": [{\"question\": \"Q\", \"options\": {\"A\": \"1\", \"B\": \"2\", \"C\": \"3\", \"D\": \"4\"}, \"correct\": \"A\", \"explanation\": \"Because it is right.\"}], \"topic\": \"AI\"}\n```"
        parsed = None

    class FakeClient:
        class models:
            @staticmethod
            def generate_content(**kwargs):
                return FakeResponse()

    service.client = FakeClient()
    result = service.generate_structured("prompt", api.QuizResponse)
    assert result.topic == "AI"
    assert len(result.quiz) == 1


def test_quiz_rejects_blank_uploaded_document():
    response = client.post(
        "/api/quiz",
        data={"topic": "", "language": "English"},
        files={"file": ("blank.pdf", make_blank_pdf(), "application/pdf")},
    )
    assert response.status_code == 422
    assert "readable" in response.json()["detail"].lower()


def test_invalid_upload_type_is_rejected():
    response = client.post(
        "/api/summary",
        data={"content": "", "language": "English"},
        files={"file": ("notes.txt", b"hello world", "text/plain")},
    )
    assert response.status_code == 415


def test_oversized_upload_is_rejected():
    oversized = b"A" * (6 * 1024 * 1024)
    response = client.post(
        "/api/summary",
        data={"content": "", "language": "English"},
        files={"file": ("big.pdf", oversized, "application/pdf")},
    )
    assert response.status_code == 413


def test_empty_upload_is_rejected():
    response = client.post(
        "/api/summary",
        data={"content": "", "language": "English"},
        files={"file": ("empty.pdf", b"", "application/pdf")},
    )
    assert response.status_code == 400

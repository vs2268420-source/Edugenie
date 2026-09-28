from fastapi.testclient import TestClient

from app.main import app
from app.routes import api


client = TestClient(app)


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

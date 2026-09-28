import json
from typing import TypeVar

from fastapi import HTTPException
from google import genai
from google.genai import types
from pydantic import BaseModel

from app.config import Settings
from app.schemas import LearningPathResponse, QuizResponse


T = TypeVar("T", bound=BaseModel)


class GeminiService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = genai.Client(api_key=settings.gemini_api_key) if settings.gemini_api_key else None

    def _require_client(self) -> genai.Client:
        if self.client is None:
            raise HTTPException(
                status_code=503,
                detail="Gemini API is not configured. Add GEMINI_API_KEY to .env.",
            )
        return self.client

    def generate_text(self, prompt: str, *, temperature: float = 0.4) -> str:
        client = self._require_client()
        try:
            response = client.models.generate_content(
                model=self.settings.gemini_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=2048,
                ),
            )
            text = getattr(response, "text", None)
            if not text:
                raise HTTPException(status_code=502, detail="Gemini returned an empty response.")
            return text.strip()
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Gemini request failed: {exc}") from exc

    def generate_structured(self, prompt: str, schema: type[T]) -> T:
        client = self._require_client()
        try:
            response = client.models.generate_content(
                model=self.settings.gemini_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=4096,
                    response_mime_type="application/json",
                    response_schema=schema,
                ),
            )
            parsed = getattr(response, "parsed", None)
            if parsed is not None:
                if isinstance(parsed, schema):
                    return parsed
                return schema.model_validate(parsed)

            text = getattr(response, "text", "")
            if not text:
                raise HTTPException(status_code=502, detail="Gemini returned no structured output.")
            return schema.model_validate(json.loads(text))
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Gemini structured-output request failed: {exc}",
            ) from exc

    def generate_with_image(self, prompt: str, image_bytes: bytes, mime_type: str) -> str:
        client = self._require_client()
        try:
            response = client.models.generate_content(
                model=self.settings.gemini_model,
                contents=[
                    prompt,
                    types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                ],
                config=types.GenerateContentConfig(
                    temperature=0.4,
                    max_output_tokens=4096,
                ),
            )
            text = getattr(response, "text", None)
            if not text:
                raise HTTPException(status_code=502, detail="Gemini returned an empty response.")
            return text.strip()
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Gemini image request failed: {exc}") from exc

    def quiz_from_text(self, topic: str, language: str, source: str) -> QuizResponse:
        prompt = f"""
You are EduGenie, an educational assistant.
Create exactly 5 multiple-choice questions about "{topic}" using the supplied study material when present.
Write all student-facing text in {language}.
Each question must have exactly four options labeled A, B, C and D.
Only one option may be correct.
Give a short explanation for every correct answer.
Prefer questions that test understanding rather than trivia.

Study material:
{source[:30000]}
"""
        result = self.generate_structured(prompt, QuizResponse)
        return result.model_copy(update={"topic": topic})

    def learning_path(self, topic: str, level: str, goal: str, hours: int, language: str) -> LearningPathResponse:
        prompt = f"""
Create a practical 6-week personalized learning path for a student.

Topic: {topic}
Current level: {level}
Goal: {goal}
Available time: {hours} hours per week
Language: {language}

Requirements:
- Exactly 6 weeks.
- Each week needs a title, 2-4 measurable objectives, 2-4 activities,
  and one concrete checkpoint.
- Sequence concepts from foundational to applied.
- Keep the workload realistic for the stated weekly time.
- Write all student-facing text in {language}.
"""
        result = self.generate_structured(prompt, LearningPathResponse)
        return result.model_copy(update={"topic": topic, "level": level, "goal": goal})

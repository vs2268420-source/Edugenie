from typing import Literal
from pydantic import BaseModel, Field, field_validator


Language = Literal["English", "Hindi", "Kannada", "Telugu"]
Level = Literal["Beginner", "Intermediate", "Advanced"]


class AskRequest(BaseModel):
    question: str = Field(min_length=2, max_length=4000)
    language: Language = "English"

    @field_validator("question")
    @classmethod
    def clean_question(cls, value: str) -> str:
        return " ".join(value.split())


class AskResponse(BaseModel):
    answer: str


class QuizQuestion(BaseModel):
    question: str
    options: dict[str, str]
    correct: Literal["A", "B", "C", "D"]
    explanation: str


class QuizResponse(BaseModel):
    quiz: list[QuizQuestion]
    topic: str


class SummaryResponse(BaseModel):
    summary: str


class LearningPathRequest(BaseModel):
    topic: str = Field(min_length=2, max_length=200)
    current_level: Level = "Beginner"
    goal: str = Field(min_length=2, max_length=500)
    hours_per_week: int = Field(default=5, ge=1, le=60)
    language: Language = "English"


class LearningPathItem(BaseModel):
    week: int
    title: str
    objectives: list[str]
    activities: list[str]
    checkpoint: str


class LearningPathResponse(BaseModel):
    topic: str
    level: str
    goal: str
    weeks: list[LearningPathItem]

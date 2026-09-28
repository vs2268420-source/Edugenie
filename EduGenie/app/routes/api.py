from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.schemas import (
    AskRequest,
    AskResponse,
    LearningPathRequest,
    LearningPathResponse,
    QuizResponse,
    SummaryResponse,
)
from app.services.documents import (
    IMAGE_EXTENSIONS,
    extract_text,
    read_upload,
    validate_upload,
)
from app.services.gemini import GeminiService


router = APIRouter(prefix="/api", tags=["EduGenie"])
settings = get_settings()
gemini = GeminiService(settings)


@router.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest):
    prompt = f"""
You are EduGenie, a patient educational tutor.
Answer the student's question in {payload.language}.
Explain the idea clearly and at an appropriate student level.
When useful, use a short example or analogy.
Do not pretend to know facts you are uncertain about.

Student question:
{payload.question}
"""
    return AskResponse(answer=gemini.generate_text(prompt))


@router.post("/quiz", response_model=QuizResponse)
async def quiz(
    topic: str = Form(""),
    language: str = Form("English"),
    file: UploadFile | None = File(None),
):
    if language not in {"English", "Hindi", "Kannada", "Telugu"}:
        return JSONResponse(status_code=422, content={"detail": "Unsupported language."})

    source = ""
    effective_topic = topic.strip() or "the uploaded study material"

    if file is not None:
        suffix = validate_upload(file, settings.max_upload_mb * 1024 * 1024)
        data = await read_upload(file, settings.max_upload_mb * 1024 * 1024)
        if suffix in IMAGE_EXTENSIONS:
            # Quiz generation from images is handled as multimodal text extraction.
            import mimetypes
            mime = mimetypes.guess_type(file.filename or "")[0] or "image/jpeg"
            text = gemini.generate_with_image(
                f"Read this study image and extract the educational content accurately. "
                f"Return only the useful study content, in English, without commentary.",
                data,
                mime,
            )
            source = text
        else:
            source = extract_text(data, suffix)

        if not source.strip():
            raise HTTPException(
                status_code=422,
                detail="No readable study content was found in the uploaded file.",
            )

    if not topic.strip() and not source.strip():
        return JSONResponse(
            status_code=400,
            content={"detail": "Provide a topic or upload a readable study file."},
        )

    return gemini.quiz_from_text(effective_topic, language, source or "No additional study material was supplied.")


@router.post("/summary", response_model=SummaryResponse)
async def summary(
    content: str = Form(""),
    language: str = Form("English"),
    file: UploadFile | None = File(None),
):
    if language not in {"English", "Hindi", "Kannada", "Telugu"}:
        return JSONResponse(status_code=422, content={"detail": "Unsupported language."})

    source = content.strip()

    if file is not None:
        suffix = validate_upload(file, settings.max_upload_mb * 1024 * 1024)
        data = await read_upload(file, settings.max_upload_mb * 1024 * 1024)
        if suffix in IMAGE_EXTENSIONS:
            import mimetypes
            mime = mimetypes.guess_type(file.filename or "")[0] or "image/jpeg"
            source = gemini.generate_with_image(
                f"Extract the educational text and key information from this image. "
                f"Return only the extracted study content.",
                data,
                mime,
            )
        else:
            source = extract_text(data, suffix)

    if not source:
        return JSONResponse(status_code=400, content={"detail": "Provide text or upload a readable file."})

    prompt = f"""
Summarize the following study material in {language}.
Use a concise title followed by clear bullet points.
Preserve important definitions, relationships, formulas, examples, and conclusions.
Do not introduce information that is absent from the material.

Material:
{source[:30000]}
"""
    return SummaryResponse(summary=gemini.generate_text(prompt))


@router.post("/learning-path", response_model=LearningPathResponse)
def learning_path(payload: LearningPathRequest):
    return gemini.learning_path(
        payload.topic,
        payload.current_level,
        payload.goal,
        payload.hours_per_week,
        payload.language,
    )

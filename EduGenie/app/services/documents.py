from io import BytesIO
from pathlib import Path

from fastapi import HTTPException, UploadFile
from PIL import Image
from PyPDF2 import PdfReader
from docx import Document
from pptx import Presentation


ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".pptx",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
}

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def validate_upload(upload: UploadFile, max_bytes: int) -> str:
    suffix = Path(upload.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail="Unsupported file type. Use PDF, DOCX, PPTX, PNG, JPG/JPEG, or WEBP.",
        )
    return suffix


async def read_upload(upload: UploadFile, max_bytes: int) -> bytes:
    data = await upload.read()
    if not data:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(data) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File is too large. Maximum allowed size is {max_bytes // (1024 * 1024)} MB.",
        )
    return data


def extract_text(data: bytes, suffix: str) -> str:
    try:
        if suffix == ".pdf":
            reader = PdfReader(BytesIO(data))
            return "\n".join(page.extract_text() or "" for page in reader.pages).strip()

        if suffix == ".docx":
            document = Document(BytesIO(data))
            return "\n".join(p.text for p in document.paragraphs if p.text.strip()).strip()

        if suffix == ".pptx":
            presentation = Presentation(BytesIO(data))
            chunks: list[str] = []
            for slide in presentation.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text.strip():
                        chunks.append(shape.text.strip())
            return "\n".join(chunks).strip()

        if suffix in IMAGE_EXTENSIONS:
            # Validate that the bytes are a real image.
            with Image.open(BytesIO(data)) as image:
                image.verify()
            return ""

    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Could not read the uploaded file: {exc}",
        ) from exc

    raise HTTPException(status_code=415, detail="Unsupported file format.")

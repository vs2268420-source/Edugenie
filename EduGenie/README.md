# EduGenie — Google Gemini Powered Learning Assistant

EduGenie is a full-stack educational assistant built with **FastAPI, Jinja2, vanilla JavaScript, and Google Gemini**.

## Features

- AI-powered student question answering
- Simple topic explanations
- 5-question multiple-choice quiz generation
- Quiz scoring with explanations
- Study-material summarization
- Personalized learning-path recommendations
- PDF, DOCX, PPTX, and image uploads for quiz/summarization
- Language selection: English, Hindi, Kannada, Telugu
- Structured Gemini JSON output for reliable quiz parsing
- File-size/type validation
- Automated tests for API behavior without requiring a Gemini key

The supplied project index identifies EduGenie as the Google Gemini Powered Learning Assistant. The accessible public material matching the project describes question answering, simple explanations, summarization, quiz generation, personalized learning paths, FastAPI REST APIs, and a responsive HTML/Jinja2 interface.

## Project structure

```text
EduGenie/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── schemas.py
│   ├── routes/
│   │   ├── __init__.py
│   │   └── api.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── gemini.py
│   │   └── documents.py
│   ├── templates/
│   │   └── index.html
│   └── static/
│       ├── css/style.css
│       └── js/app.js
├── tests/
│   ├── __init__.py
│   └── test_api.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Requirements

- Python 3.11+
- VS Code
- A Google Gemini API key

The application uses Google's current `google-genai` Python SDK. Gemini model names are configurable with `GEMINI_MODEL`; the default is `gemini-2.5-flash`.

## 1. Open in VS Code

Extract the project, then:

```bash
cd EduGenie
code .
```

## 2. Create a virtual environment

### Windows PowerShell

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
```

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 4. Configure Gemini

Copy `.env.example` to `.env`.

Windows:

```powershell
Copy-Item .env.example .env
```

macOS/Linux:

```bash
cp .env.example .env
```

Then edit `.env`:

```env
GEMINI_API_KEY=your_real_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash
MAX_UPLOAD_MB=5
```

Never commit `.env`.

## 5. Run

```bash
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

FastAPI API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

## 6. Test

Run:

```bash
pytest -q
```

The automated tests do not call Gemini. They test validation, health behavior, and API routing with a mocked AI service.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Web application |
| GET | `/health` | Health/configuration check |
| POST | `/api/ask` | Answer a student question |
| POST | `/api/quiz` | Generate a 5-question quiz |
| POST | `/api/summary` | Summarize text or an uploaded document |
| POST | `/api/learning-path` | Generate a personalized learning path |

### Ask

```json
{
  "question": "Explain photosynthesis simply.",
  "language": "English"
}
```

### Quiz

Multipart form fields:

```text
topic=Photosynthesis
language=English
file=<optional PDF/DOCX/PPTX/image>
```

### Summary

Multipart form fields:

```text
content=<optional study material>
language=English
file=<optional PDF/DOCX/PPTX/image>
```

### Learning path

```json
{
  "topic": "Python programming",
  "current_level": "Beginner",
  "goal": "Build web applications",
  "hours_per_week": 6,
  "language": "English"
}
```

## Supported uploads

- PDF
- DOCX
- PPTX
- PNG
- JPG/JPEG
- WEBP

Maximum size defaults to 5 MB and can be changed through `MAX_UPLOAD_MB`.

## Architecture

```text
Browser
   │
   ▼
FastAPI + Jinja2
   │
   ├── Validation / schemas
   ├── Document extraction
   └── Gemini service
            │
            ▼
       Google Gemini API
```

The Gemini API key stays on the server and is never exposed to browser JavaScript.

## Notes

- AI output can contain mistakes. EduGenie is an educational assistant, not an authoritative academic source.
- For production deployment, add authentication, rate limiting, persistent storage, monitoring, and a managed secrets service.
- If the configured Gemini model is unavailable for your account, set `GEMINI_MODEL` to a model available to your Gemini API project.

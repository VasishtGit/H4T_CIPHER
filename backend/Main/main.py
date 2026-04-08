import asyncio
import base64
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from supabase import Client, create_client

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DESCRIPTION_MODEL_NAME = os.getenv("DESCRIPTION_MODEL_NAME", "nvidia/nemotron-nano-12b-v2-vl:free")
SOLVER_MODEL_NAME = os.getenv("SOLVER_MODEL_NAME", DESCRIPTION_MODEL_NAME)

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SESSION_COOKIE_NAME = os.getenv("SESSION_COOKIE_NAME", "h4t_session")
IMAGE_BUCKET = os.getenv("SUPABASE_IMAGE_BUCKET", "Image")

ALLOWED_ORIGINS = [
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "null",
    "https://h4-t-cipher.vercel.app"
]

DESCRIPTION_PROMPT = (
    "You are an expert exam-question parser.\n"
    "Given a question image, return a clean structured description with:\n"
    "1. Exact extracted text\n"
    "2. Graph/chart details (axes, labels, values, units, trend)\n"
    "3. Interpreted question statement\n"
    "4. Multiple-choice options if present\n"
    "Do not solve the question."
)

SOLVER_PROMPT = (
    "You are an expert math tutor.\n"
    "Use the provided structured description of a question/graph.\n"
    "Solve step-by-step, verify result, and provide a FINAL ANSWER section."
)

if not OPENROUTER_API_KEY:
    raise RuntimeError("OPENROUTER_API_KEY must be set in environment.")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set in environment.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
app = FastAPI(title="H4T Question Parser")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _extract_user_from_auth_response(response: Any) -> dict:
    user = getattr(response, "user", None)
    if user is None and isinstance(response, dict):
        user = response.get("user")
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication failed.")

    if hasattr(user, "model_dump"):
        return user.model_dump()
    if hasattr(user, "dict"):
        return user.dict()
    if isinstance(user, dict):
        return user
    return dict(user)


def _get_user_from_token(access_token: str) -> dict:
    try:
        response = supabase.auth.get_user(access_token)
    except TypeError:
        response = supabase.auth.get_user(jwt=access_token)
    return _extract_user_from_auth_response(response)


def _get_current_user(request: Request) -> dict:
    auth_header = request.headers.get("Authorization") or ""
    token = ""
    if auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1].strip()

    if not token:
        # Backward-compatible fallback while migrating clients.
        token = request.cookies.get(SESSION_COOKIE_NAME) or ""

    if not token:
        raise HTTPException(status_code=401, detail="No token")

    try:
        return _get_user_from_token(token)
    except Exception as exc:
        raise HTTPException(status_code=401, detail=f"Invalid session: {exc}") from exc


async def call_api(client: httpx.AsyncClient, payload: dict, headers: dict, retries: int = 3):
    for i in range(retries):
        try:
            return await client.post(OPENROUTER_URL, headers=headers, json=payload)
        except httpx.ReadTimeout:
            if i == retries - 1:
                raise
            print(f"[Retry {i + 1}] Timeout... retrying")
            await asyncio.sleep(2)


def _extract_message_content(result: dict) -> str:
    choices = result.get("choices") if isinstance(result, dict) else None
    if not choices or not isinstance(choices, list):
        raise HTTPException(status_code=502, detail="OpenRouter response missing choices.")

    message = choices[0].get("message", {}) if isinstance(choices[0], dict) else {}
    content = message.get("content")
    if not content:
        raise HTTPException(status_code=502, detail="OpenRouter response missing message content.")

    if isinstance(content, list):
        text_parts: list[str] = []
        for part in content:
            if isinstance(part, str):
                if part.strip():
                    text_parts.append(part.strip())
                continue

            if not isinstance(part, dict):
                continue

            candidate = (
                part.get("text")
                or part.get("content")
                or part.get("value")
                or part.get("output_text")
            )
            if isinstance(candidate, str) and candidate.strip():
                text_parts.append(candidate.strip())

        content = "\n".join(text_parts).strip()

    if not content:
        raise HTTPException(status_code=502, detail="OpenRouter returned empty content.")

    return content


def _upload_bytes_to_supabase(bucket: str, path: str, content: bytes, content_type: str) -> str:
    try:
        supabase.storage.from_(bucket).upload(
            path=path,
            file=content,
            file_options={"content-type": content_type, "upsert": False},
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Supabase upload failed: {exc}") from exc

    url_result = supabase.storage.from_(bucket).get_public_url(path)
    if isinstance(url_result, str):
        return url_result
    if isinstance(url_result, dict):
        return url_result.get("publicUrl") or url_result.get("publicURL") or ""
    if hasattr(url_result, "get"):
        return url_result.get("publicUrl") or url_result.get("publicURL") or ""
    return str(url_result)


@app.get("/me")
def me(request: Request):
    user = _get_current_user(request)
    metadata = user.get("user_metadata") or {}
    email = user.get("email", "")
    full_name = metadata.get("full_name") or (email.split("@")[0] if email else "User")
    return {
        "user": {
            "id": user.get("id"),
            "email": email,
            "full_name": full_name,
        }
    }


@app.post("/upload")
async def upload_image(request: Request, image: UploadFile = File(...)):
    user = _get_current_user(request)
    user_id = user.get("id")

    print(f"Received upload request at {datetime.now().isoformat()}")
    image_bytes = await image.read()

    if len(image_bytes) > 5_000_000:
        raise HTTPException(status_code=400, detail="Image too large")

    image_b64 = base64.b64encode(image_bytes).decode("utf-8")
    mime_type = image.content_type or "image/png"

    image_extension = Path(image.filename or "question.png").suffix or ".png"
    image_path = f"{user_id}/images/{uuid.uuid4().hex}{image_extension}"
    graph_url = _upload_bytes_to_supabase(
        bucket=IMAGE_BUCKET,
        path=image_path,
        content=image_bytes,
        content_type=mime_type,
    )

    description_payload = {
        "model": DESCRIPTION_MODEL_NAME,
        "temperature": 0.2,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": DESCRIPTION_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime_type};base64,{image_b64}"},
                    },
                ],
            }
        ],
    }

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    timeout = httpx.Timeout(timeout=60.0, connect=10.0, read=60.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        print(f"Sending description request to OpenRouter at {datetime.now().isoformat()}")
        desc_res = await call_api(client, description_payload, headers, retries=3)
        print(f"Received description response at {datetime.now().isoformat()}")
        print(f"Description status={desc_res.status_code}, body chars={len(desc_res.text)}")

    try:
        desc_result = desc_res.json()
    except ValueError as exc:
        print(f"Description non-JSON body preview: {desc_res.text[:500]}")
        raise HTTPException(status_code=502, detail="OpenRouter returned non-JSON response.") from exc

    if desc_res.status_code >= 400:
        error_message = (
            desc_result.get("error", {}).get("message") if isinstance(desc_result, dict) else None
        )
        raise HTTPException(
            status_code=502,
            detail=error_message or f"OpenRouter description error (status {desc_res.status_code}).",
        )

    try:
        description_text = _extract_message_content(desc_result)
    except HTTPException:
        print(f"Description parse failure payload preview: {str(desc_result)[:1200]}")
        raise

    solver_payload = {
        "model": SOLVER_MODEL_NAME,
        "temperature": 0.2,
        "messages": [
            {
                "role": "user",
                "content": f"{SOLVER_PROMPT}\n\nStructured description:\n{description_text}",
            }
        ],
    }

    async with httpx.AsyncClient(timeout=timeout) as client:
        print(f"Sending solver request to OpenRouter at {datetime.now().isoformat()}")
        solve_res = await call_api(client, solver_payload, headers, retries=3)
        print(f"Received solver response at {datetime.now().isoformat()}")

    try:
        solve_result = solve_res.json()
    except ValueError as exc:
        raise HTTPException(status_code=502, detail="OpenRouter solver returned non-JSON response.") from exc

    if solve_res.status_code >= 400:
        error_message = (
            solve_result.get("error", {}).get("message") if isinstance(solve_result, dict) else None
        )
        raise HTTPException(
            status_code=502,
            detail=error_message or f"OpenRouter solver error (status {solve_res.status_code}).",
        )

    solution_text = _extract_message_content(solve_result)

    return {
        "model": SOLVER_MODEL_NAME,
        "description_model": DESCRIPTION_MODEL_NAME,
        "solver_model": SOLVER_MODEL_NAME,
        "description": description_text,
        "analysis": solution_text,
        "graph_url": graph_url,
        "user_id": user_id,
    }

@app.get("/health", methods=["GET", "HEAD"])
async def health_check():
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)

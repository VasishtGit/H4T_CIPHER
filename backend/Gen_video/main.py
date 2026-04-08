import fastapi
from fastapi import UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, FileResponse
import httpx
import base64
import os
import time
import threading
import uuid
from typing import Any
from dotenv import load_dotenv
from supabase import Client, create_client
from video_generator import execute_manim_code

load_dotenv()

app = fastapi.FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "null",
        "https://h4-t-cipher.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Length", "Content-Range", "Accept-Ranges", "Content-Type"],
)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
MODEL_NAME = "nvidia/nemotron-nano-12b-v2-vl:free"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SESSION_COOKIE_NAME = os.getenv("SESSION_COOKIE_NAME", "h4t_session")
VIDEO_BUCKET = os.getenv("SUPABASE_VIDEO_BUCKET", "Videos")

if not OPENROUTER_API_KEY:
    raise RuntimeError("OPENROUTER_API_KEY must be set in environment.")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set in environment.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

FIX_CODE_PROMPT = (
    "You are an expert Python + Manim code fixer.\n"
    "You will receive a broken Manim script.\n"
    "Return ONLY corrected, runnable Manim Python code.\n"
    "Rules:\n"
    "- Keep exactly one Scene class\n"
    "- Do NOT use MathTex, Tex, or any LaTeX objects\n"
    "- Use only Text/VGroup/Write/FadeIn/Transform\n"
    "- No markdown fences, no explanation, code only\n"
)

PROMPT = (
    "You are an expert math teacher and Manim developer.\n"
    "You are given:\n"
    "1. A math problem image\n"
    "2. A human-written explanation of the answer\n\n"
    "Your job:\n"
    "- Understand the problem from the image\n"
    "- Use the given explanation\n"
    "- Convert it into a clear step-by-step animated explanation\n"
    "- Output ONLY Manim Python code\n\n"
    "Rules:\n"
    "- Do NOT use MathTex, Tex, or any LaTeX-based objects\n"
    "- Use only Text (or VGroup of Text) for all on-screen content\n"
    "- Use Write, FadeIn, Transform animations\n"
    "- Keep steps clean and sequential\n"
    "- No extra text, only code\n"
)


def _openrouter_headers() -> dict:
    return {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8001",
        "X-Title": "Math Video Generator"
    }


async def _call_openrouter(payload: dict, request_id: str):
    async with httpx.AsyncClient() as client:
        print(f"[DEBUG][{request_id}] Sending request to OpenRouter at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        res = await client.post(OPENROUTER_URL, headers=_openrouter_headers(), json=payload)
        print(f"[DEBUG][{request_id}] Received OpenRouter response at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"[DEBUG][{request_id}] OpenRouter status={res.status_code}, body chars={len(res.text)}")
    return res


def _extract_user_from_auth_response(response: Any) -> dict:
    user = getattr(response, "user", None)
    if user is None and isinstance(response, dict):
        user = response.get("user")
    if user is None:
        raise fastapi.HTTPException(status_code=401, detail="Authentication failed.")

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
        raise fastapi.HTTPException(status_code=401, detail="No token")

    try:
        return _get_user_from_token(token)
    except Exception as exc:
        raise fastapi.HTTPException(status_code=401, detail=f"Invalid session: {exc}") from exc


def _upload_video_to_supabase(user_id: str, local_video_path: str) -> str:
    video_name = f"{uuid.uuid4().hex}.mp4"
    storage_path = f"{user_id}/videos/{video_name}"

    try:
        with open(local_video_path, "rb") as fp:
            content = fp.read()
        supabase.storage.from_(VIDEO_BUCKET).upload(
            path=storage_path,
            file=content,
            file_options={"content-type": "video/mp4", "upsert": "false"},
        )
    except Exception as exc:
        raise fastapi.HTTPException(status_code=500, detail=f"Supabase video upload failed: {exc}") from exc

    url_result = supabase.storage.from_(VIDEO_BUCKET).get_public_url(storage_path)
    if isinstance(url_result, str):
        return url_result
    if isinstance(url_result, dict):
        return (
            url_result.get("publicUrl")
            or url_result.get("publicURL")
            or (url_result.get("data") or {}).get("publicUrl")
            or (url_result.get("data") or {}).get("publicURL")
            or ""
        )
    if hasattr(url_result, "get"):
        data = url_result.get("data") or {}
        return url_result.get("publicUrl") or url_result.get("publicURL") or data.get("publicUrl") or data.get("publicURL") or ""
    return str(url_result)


def _extract_openrouter_message_content(res: httpx.Response, request_id: str) -> str:
    try:
        result = res.json()
    except ValueError as exc:
        print(f"[DEBUG][{request_id}] OpenRouter non-JSON body (first 500): {res.text[:500]}")
        raise fastapi.HTTPException(status_code=502, detail="OpenRouter returned non-JSON response.") from exc

    if res.status_code >= 400:
        error_message = (
            result.get("error", {}).get("message")
            if isinstance(result, dict)
            else None
        )
        raise fastapi.HTTPException(
            status_code=502,
            detail=error_message or f"OpenRouter error (status {res.status_code}).",
        )

    choices = result.get("choices") if isinstance(result, dict) else None
    if not choices or not isinstance(choices, list):
        raise fastapi.HTTPException(status_code=502, detail="OpenRouter response missing choices.")

    message = choices[0].get("message", {}) if isinstance(choices[0], dict) else {}
    code = message.get("content")
    if not code:
        raise fastapi.HTTPException(status_code=502, detail="OpenRouter response missing message content.")

    return code

LATEST_VIDEO_PATH = None
LATEST_VIDEO_URL = None


def process_video_job(request_id, generated_code, user_id, explanation, graph_url, base_url):
    global LATEST_VIDEO_PATH, LATEST_VIDEO_URL

    try:
        video_path = execute_manim_code(generated_code, allow_safe_fallback_scene=False)

        LATEST_VIDEO_PATH = video_path
        LATEST_VIDEO_URL = None

        try:
            uploaded_url = _upload_video_to_supabase(user_id=user_id, local_video_path=video_path)
            if uploaded_url:
                LATEST_VIDEO_URL = uploaded_url
        except Exception as exc:
            print(f"[WARN][{request_id}] Upload failed: {exc}")

        if graph_url:
            try:
                backend_stream_url = f"{base_url.rstrip('/')}/video"
                supabase.table("Graph_Solution").insert(
                    {
                        "user_id": user_id,
                        "graph_url": graph_url,
                        "solution": explanation,
                        "video_link": LATEST_VIDEO_URL or backend_stream_url,
                    }
                ).execute()
            except Exception as exc:
                print(f"[WARN][{request_id}] Graph_Solution insert failed: {exc}")

        print(f"[DEBUG][{request_id}] Background render complete")

    except Exception as e:
        print(f"[ERROR][{request_id}] Background job failed: {e}")


@app.post("/generate-video-v2")
async def generate_video_v2(
    request: Request,
    image: UploadFile | None = File(None),
    explanation: str = Form(...),
    question_description: str = Form(""),
    graph_url: str = Form(""),
):
    global LATEST_VIDEO_PATH, LATEST_VIDEO_URL
    user = _get_current_user(request)
    user_id = user.get("id")
    request_id = f"v2-{uuid.uuid4().hex[:8]}"
    print(f"[DEBUG][{request_id}] Received request at {time.strftime('%Y-%m-%d %H:%M:%S')}")

    if image is None and not (question_description or "").strip():
        raise fastapi.HTTPException(status_code=400, detail="Provide either image or question_description.")

    image_bytes = b""
    image_b64 = ""
    if image is not None:
        image_bytes = await image.read()
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    prompt_text = f"{PROMPT}\n\nQuestion description:\n{question_description}\n\nExplanation:\n{explanation}"
    message_content = [
        {
            "type": "text",
            "text": prompt_text
        }
    ]

    if image is not None:
        message_content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{image.content_type};base64,{image_b64}"
                }
            }
        )

    gen_payload = {
        "model": MODEL_NAME,
        "temperature": 0.2,
        "messages": [
            {
                "role": "user",
                "content": message_content
            }
        ]
    }

    first_response = await _call_openrouter(gen_payload, request_id)
    generated_code = _extract_openrouter_message_content(first_response, request_id)

    print(f"[DEBUG][{request_id}] Initial generated code chars={len(generated_code)}")

    threading.Thread(
        target=process_video_job,
        args=(request_id, generated_code, user_id, explanation, graph_url, str(request.base_url)),
        daemon=True,
    ).start()

    return {
        "status": "processing",
        "request_id": request_id,
        "api": "generate-video-v2",
    }


@app.get("/video")
def stream_video():
    if LATEST_VIDEO_URL:
        return RedirectResponse(url=LATEST_VIDEO_URL, status_code=307)

    if not LATEST_VIDEO_PATH or not os.path.exists(LATEST_VIDEO_PATH):
        raise fastapi.HTTPException(status_code=404, detail="No generated video found.")

    # Fallback for local playback when Supabase URL is unavailable.
    return FileResponse(LATEST_VIDEO_PATH, media_type="video/mp4")

@app.get("/")
async def root():
    return {"message": "ok"}

@app.api_route("/health", methods=["GET", "HEAD"])
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=False)
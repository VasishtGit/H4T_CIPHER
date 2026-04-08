import os
import time
from typing import Any

import fastapi
from fastapi import Body
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SESSION_COOKIE_NAME = os.getenv("SESSION_COOKIE_NAME", "h4t_session")
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

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set in environment.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
app = fastapi.FastAPI(title="H4T Auth Service")

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


def _token_from_request(request: fastapi.Request) -> str:
    auth_header = request.headers.get("Authorization") or ""
    if auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1].strip()
        if token:
            return token

    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token:
        return token

    raise fastapi.HTTPException(status_code=401, detail="No token")


def _user_payload(user: dict) -> dict:
    metadata = user.get("user_metadata") or {}
    email = user.get("email", "")
    full_name = metadata.get("full_name") or (email.split("@")[0] if email else "User")
    return {
        "id": user.get("id"),
        "email": email,
        "full_name": full_name,
    }


@app.post("/signup")
def signup(payload: dict = Body(...)):
    full_name = (payload.get("full_name") or "").strip()
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""

    if not full_name or not email or not password:
        raise fastapi.HTTPException(status_code=400, detail="full_name, email and password are required.")

    try:
        sign_up = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {"data": {"full_name": full_name}},
        })

        sign_in = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

    except Exception as exc:
        raise fastapi.HTTPException(status_code=400, detail=f"Signup failed: {exc}") from exc

    session = getattr(sign_in, "session", None)
    if not session or not session.access_token:
        raise fastapi.HTTPException(status_code=401, detail="Signup succeeded but login failed.")

    user = _extract_user_from_auth_response(sign_in)

    try:
        supabase.table("Authentication").insert({
            "auth_id": user.id,
            "email": email,
            "password": password
        }).execute()
    except Exception as e:
        print("DB insert failed:", e)

    response = fastapi.responses.JSONResponse({
        "user": _user_payload(user),
        "access_token": session.access_token,
        "message": "Signup successful"
    })
    return response


@app.post("/login")
def login(payload: dict = Body(...)):
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""
    if not email or not password:
        raise fastapi.HTTPException(status_code=400, detail="email and password are required.")

    try:
        sign_in = supabase.auth.sign_in_with_password({"email": email, "password": password})
    except Exception as exc:
        raise fastapi.HTTPException(status_code=401, detail=f"Login failed: {exc}") from exc

    session = getattr(sign_in, "session", None)
    if session is None or not getattr(session, "access_token", None):
        raise fastapi.HTTPException(status_code=401, detail="Invalid credentials.")

    user = _extract_user_from_auth_response(sign_in)
    return {
        "user": _user_payload(user),
        "access_token": session.access_token,
        "message": "Login successful",
    }


@app.post("/logout")
def logout():
    response = fastapi.responses.JSONResponse({"message": "Logged out"})
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")
    return response


@app.get("/me")
def me(request: fastapi.Request):
    token = _token_from_request(request)

    try:
        user = _get_user_from_token(token)
    except Exception as exc:
        raise fastapi.HTTPException(status_code=401, detail=f"Invalid session: {exc}") from exc

    return {"user": _user_payload(user)}


@app.get("/")
async def root():
    return {"message": time.strftime("Hello! The server is up and running at %Y-%m-%d %H:%M:%S")}

@app.get("/health")
async def health_check():
    return {
        "status": "ok"
    }

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=False)

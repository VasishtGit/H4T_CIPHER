import os
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
    raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
app = fastapi.FastAPI(title="H4T Auth Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------ HELPERS ------------------

def _extract_user_from_auth_response(response: Any) -> dict:
    user = getattr(response, "user", None)
    if user is None and isinstance(response, dict):
        user = response.get("user")

    if user is None:
        raise fastapi.HTTPException(status_code=401, detail="Auth failed")

    if hasattr(user, "model_dump"):
        return user.model_dump()
    if hasattr(user, "dict"):
        return user.dict()
    return dict(user)


def _get_user_from_token(access_token: str) -> dict:
    response = supabase.auth.get_user(access_token)
    return _extract_user_from_auth_response(response)


def _token_from_request(request: fastapi.Request) -> str:
    auth_header = request.headers.get("Authorization") or ""

    if auth_header.lower().startswith("bearer "):
        return auth_header.split(" ", 1)[1].strip()

    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token:
        return token

    raise fastapi.HTTPException(status_code=401, detail="No token")


def _user_payload(user: dict) -> dict:
    metadata = user.get("user_metadata") or {}
    email = user.get("email", "")

    return {
        "id": user.get("id"),
        "email": email,
        "full_name": metadata.get("full_name") or email.split("@")[0],
    }

# ------------------ AUTH ------------------

@app.post("/signup")
def signup(payload: dict = Body(...)):
    full_name = payload.get("full_name", "").strip()
    email = payload.get("email", "").strip().lower()
    password = payload.get("password", "")

    if not full_name or not email or not password:
        raise fastapi.HTTPException(400, "Missing fields")

    try:
        supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {"data": {"full_name": full_name}},
        })

        sign_in = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

    except Exception as e:
        raise fastapi.HTTPException(400, f"Signup failed: {e}")

    session = sign_in.session
    if not session or not session.access_token:
        raise fastapi.HTTPException(401, "Login failed after signup")

    user = _extract_user_from_auth_response(sign_in)

    return {
        "user": _user_payload(user),
        "access_token": session.access_token,
        "message": "Signup successful"
    }


@app.post("/login")
def login(payload: dict = Body(...)):
    email = payload.get("email", "").strip().lower()
    password = payload.get("password", "")

    if not email or not password:
        raise fastapi.HTTPException(400, "Missing credentials")

    try:
        sign_in = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
    except Exception as e:
        raise fastapi.HTTPException(401, f"Login failed: {e}")

    session = sign_in.session
    if not session or not session.access_token:
        raise fastapi.HTTPException(401, "Invalid credentials")

    user = _extract_user_from_auth_response(sign_in)

    return {
        "user": _user_payload(user),
        "access_token": session.access_token,
        "message": "Login successful"
    }

# ------------------ USER ------------------

@app.get("/me")
def me(request: fastapi.Request):
    token = _token_from_request(request)
    user = _get_user_from_token(token)
    return {"user": _user_payload(user)}

# ------------------ MISC ------------------

@app.post("/logout")
def logout():
    response = fastapi.responses.JSONResponse({"message": "Logged out"})
    response.delete_cookie(SESSION_COOKIE_NAME)
    return response


@app.get("/")
def root():
    return {"message": "ok"}


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8002)
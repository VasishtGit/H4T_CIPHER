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
SIGNUP_OTP_WINDOW_SECONDS = 300
PENDING_SIGNUPS: dict[str, dict] = {}

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


def _cleanup_pending_signups() -> None:
    now = time.time()
    expired_emails = [
        email
        for email, payload in PENDING_SIGNUPS.items()
        if payload.get("expires_at", 0) <= now
    ]
    for email in expired_emails:
        PENDING_SIGNUPS.pop(email, None)


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


@app.post("/send-otp")
def send_otp(payload: dict = Body(...)):
    email = (payload.get("email") or "").strip().lower()
    full_name = (payload.get("full_name") or "").strip()
    create_user = payload.get("create_user")

    if not email:
        raise fastapi.HTTPException(status_code=400, detail="email is required.")

    otp_payload = {
        "email": email,
        "options": {
            "should_create_user": True if create_user is None else bool(create_user),
        },
    }
    if full_name:
        otp_payload["options"]["data"] = {"full_name": full_name}

    try:
        supabase.auth.sign_in_with_otp(otp_payload)
    except Exception as exc:
        raise fastapi.HTTPException(status_code=400, detail=f"Failed to send OTP: {exc}") from exc

    return {"message": "OTP sent"}


@app.post("/signup/send-otp")
def send_signup_otp(payload: dict = Body(...)):
    _cleanup_pending_signups()

    full_name = (payload.get("full_name") or "").strip()
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""

    if not full_name or not email or not password:
        raise fastapi.HTTPException(status_code=400, detail="full_name, email and password are required.")
    if len(password) < 8:
        raise fastapi.HTTPException(status_code=400, detail="Password must be at least 8 characters.")

    expires_at = time.time() + SIGNUP_OTP_WINDOW_SECONDS
    PENDING_SIGNUPS[email] = {
        "full_name": full_name,
        "password": password,
        "expires_at": expires_at,
    }

    try:
        supabase.auth.sign_in_with_otp({
            "email": email,
            "options": {
                "should_create_user": True,
                "data": {"full_name": full_name},
            },
        })
    except Exception as exc:
        PENDING_SIGNUPS.pop(email, None)
        raise fastapi.HTTPException(status_code=400, detail=f"Failed to send signup OTP: {exc}") from exc

    return {
        "message": "OTP sent",
        "expires_in": SIGNUP_OTP_WINDOW_SECONDS,
    }


@app.post("/signup/verify-otp")
def verify_signup_otp(payload: dict = Body(...)):
    _cleanup_pending_signups()

    email = (payload.get("email") or "").strip().lower()
    token = (payload.get("token") or "").strip()

    if not email or not token:
        raise fastapi.HTTPException(status_code=400, detail="email and token are required.")

    pending = PENDING_SIGNUPS.get(email)
    if not pending:
        raise fastapi.HTTPException(status_code=400, detail="Signup OTP expired. Please request OTP again.")

    if pending.get("expires_at", 0) <= time.time():
        PENDING_SIGNUPS.pop(email, None)
        raise fastapi.HTTPException(status_code=400, detail="Signup OTP expired. Please request OTP again.")

    try:
        verify_response = supabase.auth.verify_otp({
            "email": email,
            "token": token,
            "type": "email",
        })
    except Exception as exc:
        raise fastapi.HTTPException(status_code=401, detail=f"Invalid OTP: {exc}") from exc

    session = getattr(verify_response, "session", None)
    if not session or not getattr(session, "access_token", None):
        raise fastapi.HTTPException(status_code=401, detail="Invalid OTP")

    user = _extract_user_from_auth_response(verify_response)

    try:
        admin_api = getattr(supabase.auth, "admin", None)
        if admin_api and hasattr(admin_api, "update_user_by_id"):
            admin_api.update_user_by_id(
                user.get("id"),
                {
                    "password": pending["password"],
                    "user_metadata": {"full_name": pending["full_name"]},
                },
            )
        else:
            raise RuntimeError("Supabase admin API unavailable for password update.")
    except Exception as exc:
        raise fastapi.HTTPException(status_code=500, detail=f"OTP verified, but password setup failed: {exc}") from exc
    finally:
        PENDING_SIGNUPS.pop(email, None)

    return {
        "access_token": session.access_token,
        "refresh_token": getattr(session, "refresh_token", None),
        "user": _user_payload(user),
        "message": "Signup successful",
    }


@app.post("/verify-otp")
def verify_otp(payload: dict = Body(...)):
    email = (payload.get("email") or "").strip().lower()
    token = (payload.get("token") or "").strip()
    token_type = (payload.get("type") or "email").strip() or "email"

    if not email or not token:
        raise fastapi.HTTPException(status_code=400, detail="email and token are required.")

    try:
        verify_response = supabase.auth.verify_otp({
            "email": email,
            "token": token,
            "type": token_type,
        })
    except Exception as exc:
        raise fastapi.HTTPException(status_code=401, detail=f"Invalid OTP: {exc}") from exc

    session = getattr(verify_response, "session", None)
    if not session or not getattr(session, "access_token", None):
        raise fastapi.HTTPException(status_code=401, detail="Invalid OTP")

    user = _extract_user_from_auth_response(verify_response)
    return {
        "access_token": session.access_token,
        "refresh_token": getattr(session, "refresh_token", None),
        "user": _user_payload(user),
        "message": "OTP verified",
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
    return {"message": "ok"}

@app.api_route("/health", methods=["GET", "HEAD"])
async def health_check():
    return {"status": "ok"}

#i am bored so i am tpying anything

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=False)

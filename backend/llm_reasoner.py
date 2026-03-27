import base64
import json
import os
import re
from typing import Any, Dict, List

import cv2
import requests


class LLMGraphReasoner:
    """Local multimodal LLM reasoner via Ollama API."""

    def __init__(self, model: str = "moondream", base_url: str = "http://127.0.0.1:11434"):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.max_image_side = int(os.getenv("GRAPH_MAX_IMAGE_SIDE", "640"))
        self.max_ocr_chars = int(os.getenv("GRAPH_MAX_OCR_CHARS", "320"))
        self.num_predict_image = int(os.getenv("GRAPH_IMAGE_NUM_PREDICT", "96"))
        self.num_predict_text = int(os.getenv("GRAPH_TEXT_NUM_PREDICT", "72"))
        self.num_ctx = int(os.getenv("GRAPH_NUM_CTX", "1024"))
        self.connect_timeout = float(os.getenv("GRAPH_CONNECT_TIMEOUT", "8"))
        self.read_timeout_image = float(os.getenv("GRAPH_IMAGE_TIMEOUT", "45"))
        self.read_timeout_text = float(os.getenv("GRAPH_TEXT_TIMEOUT", "25"))

    def _resize_if_needed(self, img):
        h, w = img.shape[:2]
        max_side = max(h, w)
        if max_side <= self.max_image_side:
            return img

        scale = float(self.max_image_side) / float(max_side)
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))
        return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

    def _image_to_base64(self, img) -> str:
        img = self._resize_if_needed(img)
        ok, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        if not ok:
            raise ValueError("Failed to encode image")
        return base64.b64encode(buf.tobytes()).decode("utf-8")

    def _extract_json(self, text: str) -> Dict[str, Any]:
        text = (text or "").strip()
        if not text:
            return {}

        # Try direct parse first.
        try:
            data = json.loads(text)
            if isinstance(data, dict):
                return data
        except Exception:
            pass

        # Fallback: parse the first JSON object block.
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            return {}

        try:
            data = json.loads(match.group(0))
            if isinstance(data, dict):
                return data
        except Exception:
            return {}

        return {}

    def _normalize_result(self, data: Dict[str, Any], raw_response: str) -> Dict[str, Any]:
        steps = data.get("steps")
        if not isinstance(steps, list):
            steps = []

        cleaned_steps: List[str] = [str(s).strip() for s in steps if str(s).strip()]
        if not cleaned_steps and raw_response:
            cleaned_steps = ["1. LLM returned unstructured output.", f"2. Raw output: {raw_response[:700]}"]

        status = str(data.get("status", "ok")).lower()
        if status not in {"ok", "error"}:
            status = "ok"

        result = {
            "status": status,
            "graph_type": data.get("graph_type", "unknown"),
            "equation": data.get("equation", "Not provided"),
            "answer": data.get("answer", data.get("equation", "Not provided")),
            "steps": cleaned_steps,
            "slope": data.get("slope"),
            "y_intercept": data.get("y_intercept"),
            "x_intercept": data.get("x_intercept"),
            "raw_result": raw_response,
        }
        return result

    def solve_image(self, img, ocr_text: str = "") -> Dict[str, Any]:
        image_b64 = self._image_to_base64(img)
        ocr_text = (ocr_text or "")[: self.max_ocr_chars]

        prompt = (
            "You are a graph math solver. Use ONLY the given graph image and OCR text context. "
            "Perform graph detection and all calculations yourself. "
            "Return STRICT JSON only with keys: "
            "status, graph_type, equation, answer, slope, y_intercept, x_intercept, steps. "
            "Rules: status is ok or error. steps is an array of concise strings. "
            "If uncertain, set status=error and explain uncertainty in steps. "
            f"OCR_CONTEXT: {ocr_text}"
        )

        payload = {
            "model": self.model,
            "prompt": prompt,
            "images": [image_b64],
            "stream": False,
            "keep_alive": "20m",
            "format": "json",
            "options": {
                "temperature": 0.1,
                "top_p": 0.9,
                "num_ctx": self.num_ctx,
                "num_predict": self.num_predict_image,
            },
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=(self.connect_timeout, self.read_timeout_image),
            )
        except Exception as exc:
            return {
                "status": "error",
                "equation": "LLM service unavailable",
                "raw_result": str(exc),
                "steps": [
                    "1. Could not connect to local multimodal LLM service.",
                    "2. Ensure Ollama is running and model is pulled.",
                ],
            }

        if response.status_code != 200:
            return {
                "status": "error",
                "equation": "LLM request failed",
                "raw_result": response.text,
                "steps": [
                    "1. Local LLM service responded with an error.",
                    f"2. HTTP status: {response.status_code}",
                ],
            }

        body = response.json()
        raw_response = body.get("response", "")
        parsed = self._extract_json(raw_response)
        if not parsed:
            return {
                "status": "error",
                "equation": "LLM output parsing failed",
                "raw_result": raw_response,
                "steps": [
                    "1. LLM responded, but output was not valid JSON.",
                    "2. Try again or reduce model temperature.",
                ],
            }

        return self._normalize_result(parsed, raw_response)

    def solve_text(self, text: str) -> Dict[str, Any]:
        prompt = (
            "You are a graph math solver. Perform all calculations yourself and return STRICT JSON only with keys: "
            "status, graph_type, equation, answer, slope, y_intercept, x_intercept, steps. "
            "status must be ok or error. steps must be a list of concise strings. "
            f"INPUT_TEXT: {text}"
        )

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "keep_alive": "20m",
            "format": "json",
            "options": {
                "temperature": 0.1,
                "top_p": 0.9,
                "num_ctx": self.num_ctx,
                "num_predict": self.num_predict_text,
            },
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=(self.connect_timeout, self.read_timeout_text),
            )
        except Exception as exc:
            return {
                "status": "error",
                "equation": "LLM service unavailable",
                "raw_result": str(exc),
                "steps": [
                    "1. Could not connect to local LLM service.",
                    "2. Ensure Ollama is running and the selected model is available.",
                ],
            }

        if response.status_code != 200:
            return {
                "status": "error",
                "equation": "LLM request failed",
                "raw_result": response.text,
                "steps": [
                    "1. Local LLM service responded with an error.",
                    f"2. HTTP status: {response.status_code}",
                ],
            }

        body = response.json()
        raw_response = body.get("response", "")
        parsed = self._extract_json(raw_response)
        if not parsed:
            return {
                "status": "error",
                "equation": "LLM output parsing failed",
                "raw_result": raw_response,
                "steps": [
                    "1. LLM responded, but output was not valid JSON.",
                    "2. Retry with a clearer equation string.",
                ],
            }

        return self._normalize_result(parsed, raw_response)

import ast
import re
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path


def _extract_scene_name(manim_code: str) -> str:
	match = re.search(r"class\s+(\w+)\s*\(\s*Scene\s*\)", manim_code)
	if not match:
		raise ValueError("No Manim Scene class found in generated code.")
	return match.group(1)


def _find_rendered_video(media_dir: Path) -> Path:
	mp4_files = list(media_dir.rglob("*.mp4"))
	if not mp4_files:
		raise RuntimeError("Manim render completed but no MP4 file was found.")
	# Manim may generate multiple files; the most recently modified one is the final render.
	return max(mp4_files, key=lambda path: path.stat().st_mtime)


def _find_rendered_video_with_fallbacks(media_dir: Path, run_dir: Path) -> Path:
    search_roots = [media_dir, run_dir]
    for root in search_roots:
        mp4_files = list(root.rglob("*.mp4"))
        if mp4_files:
            return max(mp4_files, key=lambda path: path.stat().st_mtime)
    raise RuntimeError(
        "Manim render completed but no MP4 file was found in expected paths. "
        f"Checked: {media_dir} and {run_dir}"
    )

def clean_manim_code(code: str) -> str:
    print(f"[DEBUG] clean_manim_code: raw chars={len(code)}")
    code = code.strip().replace("\ufeff", "")

    # Remove markdown fences even when malformed (e.g., ```pythonfrom manim import *).
    code = code.replace("```", "")

    # Drop standalone leading language marker lines.
    code = re.sub(r"^\s*(python|py)\s*\n", "", code, flags=re.IGNORECASE)

    # Fix malformed leading tokens like "pythonfrom manim import *".
    code = re.sub(
        r"^\s*(python|py)\s*(?=(from\s+\w+|import\s+\w+|class\s+\w+\s*\(|def\s+\w+\s*\())",
        "",
        code,
        flags=re.IGNORECASE,
    )

    # If extra prose appears before the code, start at the first likely Python statement.
    first_stmt = re.search(
        r"(?m)(^from\s+\w+\s+import\s+.*$|^import\s+\w+.*$|^class\s+\w+\s*\(\s*Scene\s*\)\s*:)",
        code,
    )
    if first_stmt:
        code = code[first_stmt.start():]

    print(f"[DEBUG] clean_manim_code: sanitized chars={len(code)}")
    return code.strip()


def _has_tex_runtime_error(stderr_text: str) -> bool:
    if not stderr_text:
        return False
    markers = [
        "latex failed",
        "miktex",
        "tex installation",
        "tex_to_svg_file",
        "print_all_tex_errors",
    ]
    lower = stderr_text.lower()
    return any(marker in lower for marker in markers)


def _latex_to_text_fallback(code: str) -> str:
    # Replace TeX-based mobjects with Text to avoid runtime LaTeX dependencies.
    updated = re.sub(r"\bMathTex\s*\(", "Text(", code)
    updated = re.sub(r"\bTex\s*\(", "Text(", updated)
    # Remove common TeX line breaks from string literals so Text renders cleaner.
    updated = updated.replace(r"\\\\", " ")
    updated = updated.replace("$", "")
    return updated


def _has_syntax_error(stderr_text: str) -> bool:
    return bool(stderr_text and "syntaxerror" in stderr_text.lower())


def _append_missing_closers(code: str) -> str:
    opener_to_closer = {"(": ")", "[": "]", "{": "}"}
    closers = set(opener_to_closer.values())
    stack: list[str] = []
    in_single = False
    in_double = False
    escape = False

    for char in code:
        if escape:
            escape = False
            continue
        if char == "\\":
            escape = True
            continue
        if char == "'" and not in_double:
            in_single = not in_single
            continue
        if char == '"' and not in_single:
            in_double = not in_double
            continue
        if in_single or in_double:
            continue

        if char in opener_to_closer:
            stack.append(char)
        elif char in closers and stack and opener_to_closer[stack[-1]] == char:
            stack.pop()

    if not stack:
        return code

    suffix = "".join(opener_to_closer[ch] for ch in reversed(stack))
    print(f"[DEBUG] _append_missing_closers: appended suffix='{suffix}'")
    return code.rstrip() + suffix + "\n"


def _syntax_error_debug_snippet(code: str, err: SyntaxError) -> str:
    if not getattr(err, "lineno", None):
        return "[no line information]"

    lines = code.splitlines()
    start = max(1, err.lineno - 2)
    end = min(len(lines), err.lineno + 2)
    chunk = []
    for line_no in range(start, end + 1):
        marker = "=>" if line_no == err.lineno else "  "
        chunk.append(f"{marker} {line_no:03d}: {lines[line_no - 1]}")
    return "\n".join(chunk)


def _build_safe_fallback_scene_text(code: str) -> str:
    lines = [line.strip() for line in code.splitlines() if line.strip()]
    payload = " ".join(lines)
    payload = payload.replace('"""', '"').replace("'''", "'")
    payload = payload.replace("\t", " ")
    payload = re.sub(r"\s+", " ", payload)
    payload = payload[:700]

    return f'''from manim import *

class FallbackExplanation(Scene):
    def construct(self):
        title = Text("Generated script had syntax issues", font_size=30)
        detail = Text("Showing safe fallback summary.", font_size=24).next_to(title, DOWN, buff=0.5)
        snippet = Text({payload!r}, font_size=18).scale_to_fit_width(config.frame_width - 1.0)
        snippet.next_to(detail, DOWN, buff=0.6)
        self.play(Write(title))
        self.play(FadeIn(detail))
        self.play(FadeIn(snippet))
        self.wait(2)
'''


def _ensure_valid_python(code: str, allow_safe_fallback: bool = False) -> str:
    try:
        ast.parse(code)
        print("[DEBUG] _ensure_valid_python: AST parse passed")
        return code
    except SyntaxError as first_err:
        print(
            "[DEBUG] _ensure_valid_python: initial parse failed at "
            f"line={first_err.lineno}, offset={first_err.offset}, msg={first_err.msg}"
        )
        print("[DEBUG] Syntax snippet (initial):\n" + _syntax_error_debug_snippet(code, first_err))
        repaired = _append_missing_closers(code)
        try:
            ast.parse(repaired)
            print("[DEBUG] _ensure_valid_python: repaired AST parse passed")
            return repaired
        except SyntaxError as second_err:
            print(
                "[DEBUG] _ensure_valid_python: repaired parse failed at "
                f"line={second_err.lineno}, offset={second_err.offset}, msg={second_err.msg}"
            )
            print("[DEBUG] Syntax snippet (repaired):\n" + _syntax_error_debug_snippet(repaired, second_err))

            if allow_safe_fallback:
                print("[DEBUG] _ensure_valid_python: using safe fallback scene")
                fallback_code = _build_safe_fallback_scene_text(code)
                ast.parse(fallback_code)
                return fallback_code

            raise


def _run_manim(run_dir: Path, media_dir: Path, scene_name: str, quality_flag: str, timeout_seconds: int):
    command = [
        sys.executable,
        "-m",
        "manim",
        quality_flag,
        "scene.py",
        scene_name,
        "--media_dir",
        str(media_dir),
    ]

    print(f"[DEBUG] Running manim command: {' '.join(command)}")
    print(f"[DEBUG] Run cwd: {run_dir}")
    start_ts = time.time()

    result = subprocess.run(
        command,
        cwd=str(run_dir),
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
    )
    elapsed = time.time() - start_ts
    print(f"[DEBUG] Manim return code: {result.returncode}, elapsed: {elapsed:.2f}s")
    return result

def execute_manim_code(
    manim_code: str,
    output_dir: str | Path = "final_videos",
    working_dir: str | Path = "manim_workspace",
    quality_flag: str = "-ql",
    timeout_seconds: int = 300,
    cleanup_temp: bool = True,
    allow_safe_fallback_scene: bool = True,
) -> str:

    manim_code = clean_manim_code(manim_code)
    manim_code = _ensure_valid_python(manim_code, allow_safe_fallback=allow_safe_fallback_scene)
    scene_name = _extract_scene_name(manim_code)
    print(f"[DEBUG] execute_manim_code: scene_name={scene_name}")

    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    working_dir = Path(working_dir).resolve()
    working_dir.mkdir(parents=True, exist_ok=True)

    # Unique ID for this run (important for concurrency)
    run_id = uuid.uuid4().hex

    # Create per-run folder
    run_dir = (working_dir / f"run_{run_id}").resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    debug_dir = run_dir / "debug"
    debug_dir.mkdir(parents=True, exist_ok=True)

    source_file = run_dir / "scene.py"
    media_dir = (run_dir / "media").resolve()

    # Save the actual Python file (persistent)
    source_file.write_text(manim_code, encoding="utf-8")
    (debug_dir / "input_code.py").write_text(manim_code, encoding="utf-8")
    print(f"[DEBUG] execute_manim_code: source chars={len(manim_code)}")

    print(f"[DEBUG] Code saved at: {source_file}")
    print(f"[DEBUG] Debug artifacts dir: {debug_dir}")

    run_result = _run_manim(run_dir, media_dir, scene_name, quality_flag, timeout_seconds)
    (debug_dir / "attempt_1_stdout.txt").write_text(run_result.stdout or "", encoding="utf-8")
    (debug_dir / "attempt_1_stderr.txt").write_text(run_result.stderr or "", encoding="utf-8")

    if run_result.returncode != 0 and _has_tex_runtime_error(run_result.stderr):
        fallback_code = _latex_to_text_fallback(manim_code)
        fallback_code = _ensure_valid_python(fallback_code, allow_safe_fallback=allow_safe_fallback_scene)
        source_file.write_text(fallback_code, encoding="utf-8")
        (debug_dir / "tex_fallback_code.py").write_text(fallback_code, encoding="utf-8")
        print("[DEBUG] TeX runtime error detected. Retrying with Text-only fallback.")
        run_result = _run_manim(run_dir, media_dir, scene_name, quality_flag, timeout_seconds)
        (debug_dir / "attempt_2_stdout.txt").write_text(run_result.stdout or "", encoding="utf-8")
        (debug_dir / "attempt_2_stderr.txt").write_text(run_result.stderr or "", encoding="utf-8")

    if run_result.returncode != 0 and _has_syntax_error(run_result.stderr):
        repaired_code = _ensure_valid_python(manim_code, allow_safe_fallback=allow_safe_fallback_scene)
        source_file.write_text(repaired_code, encoding="utf-8")
        (debug_dir / "syntax_repaired_code.py").write_text(repaired_code, encoding="utf-8")
        print("[DEBUG] SyntaxError detected from Manim run. Retrying with repaired code.")
        run_result = _run_manim(run_dir, media_dir, scene_name, quality_flag, timeout_seconds)
        (debug_dir / "attempt_3_stdout.txt").write_text(run_result.stdout or "", encoding="utf-8")
        (debug_dir / "attempt_3_stderr.txt").write_text(run_result.stderr or "", encoding="utf-8")

    if run_result.returncode != 0:
        error_message = run_result.stderr.strip() if run_result.stderr else "No stderr output."
        if run_result.stdout:
            print(f"[DEBUG] Final stdout preview (first 1000):\n{run_result.stdout[:1000]}")
        if run_result.stderr:
            print(f"[DEBUG] Final stderr preview (first 2000):\n{run_result.stderr[:2000]}")
        print(error_message)
        raise RuntimeError(f"Manim execution failed: {error_message}")

    rendered_video = _find_rendered_video_with_fallbacks(media_dir, run_dir)

    final_video_path = output_dir / f"final_{run_id}.mp4"
    shutil.move(str(rendered_video), str(final_video_path))

    if cleanup_temp:
        try:
            shutil.rmtree(run_dir, ignore_errors=True)
            print(f"[DEBUG] Cleaned temp run directory: {run_dir}")
        except Exception as cleanup_error:
            print(f"[DEBUG] Cleanup warning for {run_dir}: {cleanup_error}")

    return str(final_video_path.resolve())


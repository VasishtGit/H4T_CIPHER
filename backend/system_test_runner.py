import argparse
import json
import os
import sys
import tempfile
from dataclasses import dataclass
from typing import List, Optional

import cv2
import numpy as np

try:
    import requests
except ImportError as exc:
    raise RuntimeError("requests is required for API tests. Install with: pip install requests") from exc


@dataclass
class TestResult:
    name: str
    passed: bool
    details: str


def make_demo_graph_image(output_path: str) -> str:
    """Create a synthetic graph image for upload endpoint testing."""
    width, height = 900, 600
    img = np.ones((height, width, 3), dtype=np.uint8) * 255

    # Draw axes.
    origin = (120, 500)
    cv2.arrowedLine(img, (50, origin[1]), (850, origin[1]), (0, 0, 0), 2, tipLength=0.02)
    cv2.arrowedLine(img, (origin[0], 560), (origin[0], 60), (0, 0, 0), 2, tipLength=0.02)

    # Draw line approximating y = 2x + 3 in graph-space style.
    # Pixel-space slope is inverted because y grows downward.
    pt1 = (180, 470)
    pt2 = (520, 250)
    cv2.line(img, pt1, pt2, (220, 50, 50), 3)

    # Add equation text to help OCR and model parsing.
    cv2.putText(img, "y = 2x + 3", (560, 130), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (20, 20, 20), 3)
    cv2.putText(img, "x", (840, 535), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (20, 20, 20), 2)
    cv2.putText(img, "y", (90, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (20, 20, 20), 2)

    cv2.imwrite(output_path, img)
    return output_path


def run_text_solver_tests(base_url: str, timeout: int) -> List[TestResult]:
    results: List[TestResult] = []
    cases = [
        ("api:solve_text:linear", {"equation": "y = 2x + 3"}, "ok"),
        ("api:solve_text:quadratic", {"equation": "y = x^2 - 5x + 6"}, "ok"),
        ("api:solve_text:invalid", {"equation": "this is not an equation"}, None),
    ]

    for test_name, payload, expected_status in cases:
        try:
            response = post_json(base_url, "/solve_text", payload, timeout)
            if response.status_code != 200:
                results.append(TestResult(test_name, False, f"HTTP {response.status_code}: {response.text[:240]}"))
                continue

            body = response.json()
            solution = body.get("solution", {})
            status_ok = (
                solution.get("status") == expected_status
                if expected_status is not None
                else solution.get("status") in {"ok", "error"}
            )
            passed = (
                body.get("status") == "success"
                and status_ok
                and isinstance(solution.get("steps"), list)
                and len(solution.get("steps", [])) > 0
            )
            details = (
                f"api_status={body.get('status')}, solver_status={solution.get('status')}, "
                f"graph_type={solution.get('graph_type')}"
            )
            results.append(TestResult(test_name, passed, details))
        except Exception as exc:
            results.append(TestResult(test_name, False, f"Exception: {exc}"))

    return results


def post_json(base_url: str, path: str, payload: dict, timeout: int) -> requests.Response:
    url = f"{base_url.rstrip('/')}{path}"
    return requests.post(url, json=payload, timeout=timeout)


def post_upload(base_url: str, path: str, file_path: str, timeout: int) -> requests.Response:
    url = f"{base_url.rstrip('/')}{path}"
    with open(file_path, "rb") as f:
        files = [("images", (os.path.basename(file_path), f, "image/png"))]
        return requests.post(url, files=files, timeout=timeout)


def run_api_tests(base_url: str, image_path: Optional[str], timeout: int, skip_upload: bool) -> List[TestResult]:
    results: List[TestResult] = []
    results.extend(run_text_solver_tests(base_url, timeout))

    if skip_upload:
        results.append(TestResult("api:upload", True, "Skipped by --skip-upload"))
        return results

    temp_file = None
    try:
        if image_path:
            upload_path = image_path
        else:
            fd, temp_file = tempfile.mkstemp(suffix=".png", prefix="graph_test_")
            os.close(fd)
            upload_path = make_demo_graph_image(temp_file)

        response = post_upload(base_url, "/upload", upload_path, timeout)
        if response.status_code != 200:
            results.append(TestResult("api:upload", False, f"HTTP {response.status_code}: {response.text[:240]}"))
        else:
            body = response.json()
            solution = body.get("solution", {})
            passed = (
                body.get("status") == "success"
                and solution.get("status") == "ok"
                and isinstance(solution.get("steps"), list)
                and len(solution.get("steps", [])) > 0
                and solution.get("equation_source") is not None
            )
            details = (
                f"api_status={body.get('status')}, solver_status={solution.get('status')}, "
                f"equation_source={solution.get('equation_source')}"
            )
            results.append(TestResult("api:upload", passed, details))
    except Exception as exc:
        results.append(TestResult("api:upload", False, f"Exception: {exc}"))
    finally:
        if temp_file and os.path.exists(temp_file):
            os.remove(temp_file)

    return results


def _close_enough(actual, expected, tol):
    try:
        return abs(float(actual) - float(expected)) <= tol
    except Exception:
        return False


def run_upload_accuracy_check(
    base_url: str,
    image_path: str,
    timeout: int,
    expected_slope: Optional[float],
    expected_intercept: Optional[float],
    tolerance: float,
    expected_graph_type: Optional[str],
    expected_equation_contains: Optional[str],
) -> TestResult:
    try:
        response = post_upload(base_url, "/upload", image_path, timeout)
        if response.status_code != 200:
            return TestResult("api:upload:accuracy", False, f"HTTP {response.status_code}: {response.text[:240]}")

        body = response.json()
        solution = body.get("solution", {})
        got_m = solution.get("slope")
        got_b = solution.get("y_intercept")
        got_graph_type = solution.get("graph_type")
        got_equation = (solution.get("equation") or "")

        slope_ok = True if expected_slope is None else _close_enough(got_m, expected_slope, tolerance)
        intercept_ok = True if expected_intercept is None else _close_enough(got_b, expected_intercept, tolerance)
        graph_type_ok = True if not expected_graph_type else (str(got_graph_type).lower() == str(expected_graph_type).lower())
        equation_ok = True if not expected_equation_contains else (str(expected_equation_contains).lower() in got_equation.lower())
        passed = (
            body.get("status") == "success"
            and solution.get("status") == "ok"
            and slope_ok
            and intercept_ok
            and graph_type_ok
            and equation_ok
        )
        details = (
            f"expected(m,b)=({expected_slope},{expected_intercept}), "
            f"got(m,b)=({got_m},{got_b}), tol={tolerance}, "
            f"expected_type={expected_graph_type}, got_type={got_graph_type}, "
            f"expected_eq_contains={expected_equation_contains}, got_eq={got_equation}, "
            f"source={solution.get('equation_source')}"
        )
        return TestResult("api:upload:accuracy", passed, details)
    except Exception as exc:
        return TestResult("api:upload:accuracy", False, f"Exception: {exc}")


def print_summary(results: List[TestResult]) -> int:
    passed = [r for r in results if r.passed]
    failed = [r for r in results if not r.passed]

    print("\n=== System Test Summary ===")
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        print(f"[{status}] {r.name} -> {r.details}")

    print("\nTotals:")
    print(f"Passed: {len(passed)}")
    print(f"Failed: {len(failed)}")

    if failed:
        print("\nFailure Details JSON:")
        print(json.dumps([r.__dict__ for r in failed], indent=2))
        return 1
    return 0


def parse_args():
    parser = argparse.ArgumentParser(description="Run end-to-end tests for graph equation solver backend.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Backend API base URL")
    parser.add_argument("--image", default=None, help="Optional graph image path for /upload test")
    parser.add_argument("--timeout", type=int, default=60, help="HTTP timeout in seconds")
    parser.add_argument("--skip-api", action="store_true", help="Skip API tests and run only local solver tests")
    parser.add_argument("--skip-upload", action="store_true", help="Skip /upload test")
    parser.add_argument("--expected-slope", type=float, default=None, help="Expected slope for image accuracy check")
    parser.add_argument("--expected-intercept", type=float, default=None, help="Expected y-intercept for image accuracy check")
    parser.add_argument("--tolerance", type=float, default=0.35, help="Numeric tolerance for slope/intercept checks")
    parser.add_argument("--expected-graph-type", default=None, help="Expected graph_type for upload result (e.g., linear/quadratic/polynomial)")
    parser.add_argument("--expected-equation-contains", default=None, help="Substring expected inside solved equation")
    return parser.parse_args()


def main():
    args = parse_args()

    all_results: List[TestResult] = []

    if not args.skip_api:
        all_results.extend(run_api_tests(args.base_url, args.image, args.timeout, args.skip_upload))
        if args.image and (
            args.expected_slope is not None
            or args.expected_intercept is not None
            or args.expected_graph_type
            or args.expected_equation_contains
        ):
            all_results.append(
                run_upload_accuracy_check(
                    args.base_url,
                    args.image,
                    args.timeout,
                    args.expected_slope,
                    args.expected_intercept,
                    args.tolerance,
                    args.expected_graph_type,
                    args.expected_equation_contains,
                )
            )

    code = print_summary(all_results)
    sys.exit(code)


if __name__ == "__main__":
    main()

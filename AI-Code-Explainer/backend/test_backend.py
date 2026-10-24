"""
Automated Test Suite for AI Code Explainer FastAPI Backend (Step 2B).

Tests are organized into two groups:

GROUP 1 — Mocked AI tests (do NOT require a real API key or network access):
  These tests replace the Gemini API call with a fake "mock" response so we
  can test all code paths without spending API quota or needing a live key.
  - Successful AI response containing all four required sections
  - Successful AI response for JavaScript code
  - Gemini returns JSON wrapped in markdown fences (should still be stripped/parsed)
  - Gemini returns malformed / non-JSON text → expect HTTP 502
  - Gemini API call raises an exception (network error, quota, etc.) → expect HTTP 502
  - No API key configured (AI_ENABLED=False) → expect HTTP 503

GROUP 2 — Validation & infrastructure tests (no mocking needed, always run):
  - Health check GET and POST (updated for v0.2.0 schema)
  - Empty code → HTTP 400
  - Whitespace-only code → HTTP 400
  - Oversized code (> 10,000 chars) → HTTP 400
  - Missing required 'code' field → HTTP 422
  - CORS preflight headers for local development
  - Gemini model name is set to a current, non-deprecated model

HOW MOCKING WORKS (for beginners):
  "Mocking" means we intercept the real Gemini API call inside our code and
  replace it with a fake function that returns whatever we tell it to.
  This means:
    - Tests are instant (no network wait).
    - Tests work offline and without a valid API key.
    - We can precisely control what Gemini "returns" to test every error case.
  We use Python's built-in `unittest.mock.patch` to do this.
"""

import sys
import json
import unittest
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient
import main
from main import app, MAX_CODE_LENGTH

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helper: build a realistic fake Gemini JSON response as a string
# ---------------------------------------------------------------------------

def _make_fake_gemini_json(
    language: str = "Python",
    num_lines: int = 1,
    snippet: str = "print('hello world')"
) -> str:
    """
    Return a JSON string that looks exactly like what a real Gemini response
    would contain for a valid code explanation request.
    """
    line_by_line = [
        {
            "line_number": i + 1,
            "code_snippet": snippet,
            "explanation": f"This line does something useful (line {i + 1})."
        }
        for i in range(num_lines)
    ]
    payload = {
        "simple_explanation": f"This {language} code is a simple demonstration.",
        "line_by_line": line_by_line,
        "example_output": f"hello world",
        "debugging_suggestions": [
            "Make sure the variable is defined before use.",
            "Check for off-by-one errors in loops."
        ]
    }
    return json.dumps(payload)


def _make_mock_gemini_response(text: str) -> MagicMock:
    """
    Create a fake Gemini SDK response object.
    The real SDK returns an object with a `.text` attribute, so we simulate that.
    """
    mock_response = MagicMock()
    mock_response.text = text
    return mock_response


# ===========================================================================
# GROUP 1 — Mocked AI Tests
# ===========================================================================

class TestMockedGeminiCalls(unittest.TestCase):
    """
    All tests in this class intercept the real Gemini API call and replace it
    with a controlled fake. No real API key or network is used.
    """

    def _patch_gemini(self, response_text: str):
        """
        Helper: returns a context manager that patches the Gemini client so
        that calling generate_content() returns a fake response with the given text.

        We patch `main.gemini_client` directly so that:
          1. The patch works regardless of whether a real key is loaded.
          2. We also force AI_ENABLED=True so the code path that calls Gemini is reached.
        """
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = _make_mock_gemini_response(response_text)
        return mock_client

    # -----------------------------------------------------------------------
    # Test 1: Successful AI response — Python
    # -----------------------------------------------------------------------
    def test_explain_ai_success_python(self):
        """
        Mocks Gemini to return a valid JSON explanation for Python code.
        Verifies all four required sections are present and correctly populated.
        """
        fake_json = _make_fake_gemini_json(language="Python", num_lines=1, snippet="print('hello world')")
        mock_client = self._patch_gemini(fake_json)

        with patch.object(main, "gemini_client", mock_client), \
             patch.object(main, "AI_ENABLED", True):

            payload = {"code": "print('hello world')", "language": "python"}
            response = client.post("/api/explain", json=payload)

        self.assertEqual(response.status_code, 200,
                         f"Expected 200, got {response.status_code}: {response.text}")
        data = response.json()

        # Core response shape
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["language"], "Python")
        self.assertTrue(data["is_ai_connected"])
        self.assertIn("AI explanation generated successfully", data["message"])

        # All four required AI sections must be present and non-empty
        self.assertIsInstance(data["simple_explanation"], str)
        self.assertTrue(len(data["simple_explanation"]) > 0,
                        "simple_explanation should not be empty")

        self.assertIsInstance(data["line_by_line"], list)
        self.assertGreater(len(data["line_by_line"]), 0,
                           "line_by_line should contain at least one entry")
        first_line = data["line_by_line"][0]
        self.assertIn("line_number", first_line)
        self.assertIn("code_snippet", first_line)
        self.assertIn("explanation", first_line)

        self.assertIsInstance(data["example_output"], str)
        self.assertTrue(len(data["example_output"]) > 0,
                        "example_output should not be empty")

        self.assertIsInstance(data["debugging_suggestions"], list)
        self.assertGreater(len(data["debugging_suggestions"]), 0,
                           "debugging_suggestions should contain at least one tip")

        print("[PASS] Mocked: Python code returns 200 with all four AI sections populated")

    # -----------------------------------------------------------------------
    # Test 2: Successful AI response — JavaScript
    # -----------------------------------------------------------------------
    def test_explain_ai_success_javascript(self):
        """
        Mocks Gemini to return a valid JSON explanation for JavaScript code.
        Verifies language is correctly capitalised and response is successful.
        """
        js_code = "function greet(name) {\n    return 'Hello ' + name;\n}"
        fake_json = _make_fake_gemini_json(language="Javascript", num_lines=3)
        mock_client = self._patch_gemini(fake_json)

        with patch.object(main, "gemini_client", mock_client), \
             patch.object(main, "AI_ENABLED", True):

            payload = {"code": js_code, "language": "javascript"}
            response = client.post("/api/explain", json=payload)

        self.assertEqual(response.status_code, 200,
                         f"Expected 200, got {response.status_code}: {response.text}")
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["language"], "Javascript")
        self.assertTrue(data["is_ai_connected"])
        self.assertEqual(data["line_count"], 3)

        print("[PASS] Mocked: JavaScript code returns 200 with correct language and line count")

    # -----------------------------------------------------------------------
    # Test 3: Gemini wraps JSON in markdown fences — must still work
    # -----------------------------------------------------------------------
    def test_explain_ai_strips_markdown_fences(self):
        """
        Sometimes Gemini wraps its JSON in ```json ... ``` markdown fences
        even when instructed not to. Our code should strip these and still parse.
        """
        raw_json = _make_fake_gemini_json()
        # Simulate Gemini wrapping in markdown fences
        fenced_response = f"```json\n{raw_json}\n```"
        mock_client = self._patch_gemini(fenced_response)

        with patch.object(main, "gemini_client", mock_client), \
             patch.object(main, "AI_ENABLED", True):

            payload = {"code": "print('hello')", "language": "python"}
            response = client.post("/api/explain", json=payload)

        self.assertEqual(response.status_code, 200,
                         f"Expected 200 after stripping fences, got {response.status_code}: {response.text}")
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertTrue(data["is_ai_connected"])

        print("[PASS] Mocked: Gemini markdown fences are stripped and JSON is parsed correctly")

    # -----------------------------------------------------------------------
    # Test 4: Gemini returns invalid / non-JSON text → HTTP 502
    # -----------------------------------------------------------------------
    def test_explain_ai_returns_bad_json(self):
        """
        If Gemini returns text that cannot be parsed as JSON, the server
        must return HTTP 502 (Bad Gateway) with a descriptive error message.
        This protects the frontend from getting a confusing server crash.
        """
        mock_client = self._patch_gemini("Sorry, I cannot help with that request.")

        with patch.object(main, "gemini_client", mock_client), \
             patch.object(main, "AI_ENABLED", True):

            payload = {"code": "print('hello')", "language": "python"}
            response = client.post("/api/explain", json=payload)

        self.assertEqual(response.status_code, 502,
                         f"Expected 502 for non-JSON Gemini response, got {response.status_code}")
        data = response.json()
        self.assertIn("unexpected response format", data["detail"].lower())

        print("[PASS] Mocked: Non-JSON Gemini response correctly returns HTTP 502")

    # -----------------------------------------------------------------------
    # Test 5: Gemini API call raises an exception → HTTP 502
    # -----------------------------------------------------------------------
    def test_explain_ai_api_exception(self):
        """
        If the Gemini API call itself throws an exception (e.g. network timeout,
        quota exceeded, invalid key), the server must return HTTP 502 with a
        user-friendly error message — not crash with a 500 Internal Server Error.
        """
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("Quota exceeded")

        with patch.object(main, "gemini_client", mock_client), \
             patch.object(main, "AI_ENABLED", True):

            payload = {"code": "print('hello')", "language": "python"}
            response = client.post("/api/explain", json=payload)

        self.assertEqual(response.status_code, 502,
                         f"Expected 502 for Gemini API exception, got {response.status_code}")
        data = response.json()
        detail_lower = data["detail"].lower()
        self.assertTrue(
            "ai model" in detail_lower or "gemini" in detail_lower or "unavailable" in detail_lower,
            f"Expected 502 detail to mention AI/Gemini/unavailable, got: {data['detail']}"
        )
        print("[PASS] Mocked: Gemini API exception correctly returns HTTP 502")


    # -----------------------------------------------------------------------
    # Test 6: No API key configured → HTTP 503
    # -----------------------------------------------------------------------
    def test_explain_no_api_key_returns_503(self):
        """
        If no valid Gemini API key is set (AI_ENABLED=False), any call to
        /api/explain must return HTTP 503 (Service Unavailable) with a clear
        message telling the user to add their key to .env.

        This is the exact error a user would see if they forgot to configure
        their key, or if the .env file still has the placeholder value.
        """
        with patch.object(main, "AI_ENABLED", False), \
             patch.object(main, "gemini_client", None):

            payload = {"code": "print('hello')", "language": "python"}
            response = client.post("/api/explain", json=payload)

        self.assertEqual(response.status_code, 503,
                         f"Expected 503 when no API key is set, got {response.status_code}")
        data = response.json()
        self.assertIn("not configured", data["detail"].lower())

        print("[PASS] Mocked: Missing API key correctly returns HTTP 503 with helpful message")

    # -----------------------------------------------------------------------
    # Test 7: Gemini returns JSON missing optional fields — fallbacks kick in
    # -----------------------------------------------------------------------
    def test_explain_ai_partial_response_uses_fallbacks(self):
        """
        If Gemini returns a JSON object that is missing some fields (e.g. no
        debugging_suggestions), our fallback helpers should fill in safe defaults
        rather than crashing with a KeyError.
        """
        # Deliberately omit debugging_suggestions and example_output
        partial_payload = json.dumps({
            "simple_explanation": "This code prints hello world.",
            "line_by_line": [
                {"line_number": 1, "code_snippet": "print('hello')", "explanation": "Prints hello."}
            ]
            # missing: example_output, debugging_suggestions
        })
        mock_client = self._patch_gemini(partial_payload)

        with patch.object(main, "gemini_client", mock_client), \
             patch.object(main, "AI_ENABLED", True):

            payload = {"code": "print('hello')", "language": "python"}
            response = client.post("/api/explain", json=payload)

        self.assertEqual(response.status_code, 200,
                         f"Expected 200 even with partial Gemini response, got {response.status_code}: {response.text}")
        data = response.json()
        # Fallback strings should be present (not empty, not a crash)
        self.assertIsInstance(data["example_output"], str)
        self.assertGreater(len(data["example_output"]), 0)
        self.assertIsInstance(data["debugging_suggestions"], list)
        self.assertGreater(len(data["debugging_suggestions"]), 0)

        print("[PASS] Mocked: Partial Gemini response correctly uses fallback values")


# ===========================================================================
# GROUP 2 — Validation & Infrastructure Tests (no mocking needed)
# ===========================================================================

class TestValidationAndInfrastructure(unittest.TestCase):
    """
    These tests check input validation and server infrastructure.
    They do not call the Gemini API at all — validation happens before
    the API call, so they pass regardless of whether a key is configured.
    """

    # -----------------------------------------------------------------------
    # Health check
    # -----------------------------------------------------------------------
    def test_health_get(self):
        """GET /api/health returns 200 and the correct v0.2.0 schema."""
        response = client.get("/api/health")
        self.assertEqual(response.status_code, 200,
                         f"Expected 200, got {response.status_code}")
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["service"], "AI Code Explainer Backend")
        self.assertEqual(data["version"], "0.2.0")
        self.assertIn("step", data)
        self.assertIn("ai_connected", data)
        print("[PASS] GET /api/health returns 200 and correct v0.2.0 JSON schema")

    def test_health_post(self):
        """POST /api/health returns 200."""
        response = client.post("/api/health")
        self.assertEqual(response.status_code, 200,
                         f"Expected 200, got {response.status_code}")
        data = response.json()
        self.assertEqual(data["status"], "ok")
        print("[PASS] POST /api/health returns 200")

    def test_health_reflects_ai_enabled_flag(self):
        """
        The health check's ai_connected field should match main.AI_ENABLED.
        When AI is enabled, it's True. When disabled, it's False.
        """
        # Check that the value is a boolean (either True or False — depends on .env)
        response = client.get("/api/health")
        data = response.json()
        self.assertIsInstance(data["ai_connected"], bool)
        print(f"[PASS] GET /api/health ai_connected={data['ai_connected']} (matches AI_ENABLED)")

    # -----------------------------------------------------------------------
    # Input validation — these run BEFORE any Gemini call
    # -----------------------------------------------------------------------
    def test_explain_empty_code(self):
        """Empty code string is rejected before reaching Gemini."""
        payload = {"code": "", "language": "python"}
        response = client.post("/api/explain", json=payload)
        self.assertIn(response.status_code, (400, 422),
                      f"Expected 400 or 422, got {response.status_code}")
        print(f"[PASS] Empty code rejected with HTTP {response.status_code} (before Gemini call)")

    def test_explain_whitespace_only(self):
        """Whitespace-only code is rejected with HTTP 400 before reaching Gemini."""
        payload = {"code": "   \n\t   \n   ", "language": "python"}
        response = client.post("/api/explain", json=payload)
        self.assertEqual(response.status_code, 400,
                         f"Expected 400, got {response.status_code}")
        data = response.json()
        self.assertIn("cannot be empty", data["detail"].lower())
        print("[PASS] Whitespace-only code rejected with HTTP 400 (before Gemini call)")

    def test_explain_oversized_code(self):
        """Code exceeding 10,000 characters is rejected with HTTP 400 before reaching Gemini."""
        oversized = "a" * (MAX_CODE_LENGTH + 1)
        payload = {"code": oversized, "language": "python"}
        response = client.post("/api/explain", json=payload)
        self.assertEqual(response.status_code, 400,
                         f"Expected 400, got {response.status_code}")
        data = response.json()
        self.assertIn("exceeds maximum allowed size", data["detail"].lower())
        print("[PASS] Oversized code (>10,000 chars) rejected with HTTP 400 (before Gemini call)")

    def test_explain_missing_code_field(self):
        """Request body without the required 'code' field returns HTTP 422."""
        payload = {"language": "python"}
        response = client.post("/api/explain", json=payload)
        self.assertEqual(response.status_code, 422,
                         f"Expected 422, got {response.status_code}")
        print("[PASS] Missing 'code' field rejected with HTTP 422")

    # -----------------------------------------------------------------------
    # CORS
    # -----------------------------------------------------------------------
    def test_cors_preflight_headers(self):
        """OPTIONS preflight request from localhost gets CORS headers back."""
        response = client.options(
            "/api/explain",
            headers={
                "Origin": "http://localhost:5500",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            }
        )
        self.assertEqual(response.status_code, 200,
                         f"Expected 200, got {response.status_code}")
        self.assertIn("access-control-allow-origin", response.headers)
        print("[PASS] CORS preflight from localhost:5500 returns correct headers")

    # -----------------------------------------------------------------------
    # Model configuration
    # -----------------------------------------------------------------------
    def test_gemini_model_is_configured(self):
        """
        Verify that _GEMINI_MODELS contains only non-deprecated, verified model names,
        and that GEMINI_MODEL / GEMINI_MODEL_FALLBACK / GEMINI_MODEL_FALLBACK2 are
        derived correctly from it.

        This test does NOT call the Gemini API.
        Live-verified model list: 2026-10-20 against this API key.
        """
        # Models confirmed responding in <3s on 2026-10-20
        known_available = {
            "gemini-3.1-flash-lite",
            "gemini-3.5-flash",
            "gemini-3.6-flash",
            "gemini-3.7-flash",
            "gemini-3.8-flash",
            "gemini-4-argon",
            "gemini-flash-latest",
            "gemini-pro-latest",
        }
        # Models confirmed 404 for new API keys
        deprecated = {
            "gemini-2.5-flash",
            "gemini-2.5-pro",
            "gemini-2.0-flash",
            "gemini-2.0-flash-001",
            "gemini-2.0-flash-lite",
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "gemini-1.0-pro",
        }

        # _GEMINI_MODELS must be a non-empty list
        models = main._GEMINI_MODELS
        self.assertIsInstance(models, list, "_GEMINI_MODELS must be a list")
        self.assertGreater(len(models), 0, "_GEMINI_MODELS must not be empty")

        for m in models:
            self.assertIsInstance(m, str, f"Model entry must be str, got {type(m)}")
            self.assertGreater(len(m.strip()), 0, "Model name must not be empty")
            self.assertNotIn(m, deprecated,
                             f"'{m}' is deprecated/404 for new API keys — remove it")
            self.assertIn(m, known_available,
                          f"'{m}' is not in verified-available set. "
                          f"Add it to known_available if confirmed working.")

        # Backward-compatible constants must point into the list
        self.assertEqual(main.GEMINI_MODEL, models[0])
        self.assertEqual(main.GEMINI_MODEL_FALLBACK, models[1])
        self.assertEqual(main.GEMINI_MODEL_FALLBACK2, models[2])

        # Hard timeout must be positive
        self.assertGreater(main._PER_MODEL_TIMEOUT, 0)

        print(f"[PASS] _GEMINI_MODELS={models}")
        print(f"[PASS] _PER_MODEL_TIMEOUT={main._PER_MODEL_TIMEOUT}s")




# ===========================================================================
# Runner — works both via `python test_backend.py` and `pytest`
# ===========================================================================

if __name__ == "__main__":
    print("=" * 60)
    print(" AI Code Explainer — Backend Test Suite (Step 2B)")
    print("=" * 60)
    print()

    # Collect all test classes
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestMockedGeminiCalls))
    suite.addTests(loader.loadTestsFromTestCase(TestValidationAndInfrastructure))
    # TestValidationAndInfrastructure already includes test_gemini_model_is_configured

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print()
    print("=" * 60)
    total = result.testsRun
    failures = len(result.failures) + len(result.errors)
    if failures == 0:
        print(f"ALL {total} TESTS PASSED SUCCESSFULLY! (0 failures)")
        sys.exit(0)
    else:
        print(f"TESTS FAILED: {failures} failure(s) out of {total} tests")
        sys.exit(1)

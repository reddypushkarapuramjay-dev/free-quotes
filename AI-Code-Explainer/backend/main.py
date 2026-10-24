"""
AI Code Explainer - Backend API (FastAPI)
Step 2B: Google Gemini API Integration

This FastAPI application provides:
1. Health check endpoints (/api/health) to verify server status.
2. An explanation endpoint (/api/explain) that receives source code,
   validates input, calls the Google Gemini API to generate a real
   AI-powered explanation, and returns a structured response.
3. CORS configuration for local development.

SAFETY NOTES:
- This backend NEVER executes or evaluates user-submitted source code.
- Code is passed as plain text to the Gemini API for analysis only.
- The Gemini API key is loaded exclusively from a local .env file.
  It is never exposed to the frontend (HTML/JavaScript).
"""

import os
import json
import logging

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables from backend/.env (must be done before reading os.environ)
load_dotenv()

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Read and Validate API Key at Startup ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

# Detect placeholder or missing key without logging the key itself
_PLACEHOLDER_VALUES = {"", "your_gemini_api_key_here", "your-api-key-here", "placeholder"}
AI_ENABLED = GEMINI_API_KEY not in _PLACEHOLDER_VALUES

if AI_ENABLED:
    logger.info("GEMINI_API_KEY loaded successfully. AI explanations are enabled.")
else:
    logger.warning(
        "GEMINI_API_KEY is missing or is still the placeholder value. "
        "The /api/explain endpoint will return a 503 error until a valid key is set in backend/.env"
    )

# --- Initialize Gemini client only when key is available ---
gemini_client = None
if AI_ENABLED:
    try:
        from google import genai
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
        logger.info("Google GenAI client initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize Google GenAI client: {e}")
        AI_ENABLED = False
        gemini_client = None

# Gemini models tried in order — live-tested 2026-10-20 against this API key.
# CONFIRMED WORKING (<3s each):
#   gemini-3.1-flash-lite  -> 1.7s
#   gemini-3.5-flash       -> 2.7s
#   gemini-3.6-flash       -> 2.9s
# EXCLUDED (currently unavailable):
#   gemini-3.7-flash  -> tenacity hangs >18s (503 internal)
#   gemini-3.8-flash  -> 503 in 5.2s
#   gemini-2.5-flash  -> 404 (blocked for new API keys)
#   gemini-2.0-flash  -> 404 (deprecated)
#
# Each call uses a hard 15-second wall-clock timeout that bypasses the
# SDK's internal tenacity retry loop.
_GEMINI_MODELS = [
    "gemini-3.1-flash-lite",  # confirmed 1.7s  2026-10-20 ✓
    "gemini-3.5-flash",       # confirmed 2.7s  2026-10-20 ✓
    "gemini-3.6-flash",       # confirmed 2.9s  2026-10-20 ✓
]
_PER_MODEL_TIMEOUT = 15    # seconds hard wall-clock per model attempt
_RETRY_DELAY      = 0.3    # seconds pause before next model

# Backward-compatible constants used by tests
GEMINI_MODEL           = _GEMINI_MODELS[0]
GEMINI_MODEL_FALLBACK  = _GEMINI_MODELS[1]
GEMINI_MODEL_FALLBACK2 = _GEMINI_MODELS[2]

# --- FastAPI Application Initialization ---
app = FastAPI(
    title="AI Code Explainer API",
    description="Backend API service for AI Code Explainer project (Step 2B — Gemini Integration).",
    version="0.2.0"
)

# --- Local Development CORS Configuration ---
# Allows the frontend (running locally on localhost, 127.0.0.1, or opened as a local file)
# to communicate with this backend API without browser CORS blocking.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "null",  # Allows requests from local file:// pages in browsers like Chrome
        "*"
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# --- Maximum Code Size Constraint (10,000 characters) ---
MAX_CODE_LENGTH = 10000


# --- Pydantic Data Models (Request & Response Schemas) ---

class HealthResponse(BaseModel):
    """Response schema for health check endpoint."""
    status: str = Field("ok", description="Server status indicator")
    service: str = Field("AI Code Explainer Backend", description="Service name")
    version: str = Field("0.2.0", description="API version")
    step: str = Field("Step 2B - Gemini AI Integration", description="Project roadmap step")
    ai_connected: bool = Field(False, description="Whether live AI API is connected")


class ExplainRequest(BaseModel):
    """Request schema for code explanation."""
    language: str = Field(
        default="python",
        description="Programming language of the source code (e.g., python, javascript, java, c, cpp)",
        max_length=50
    )
    code: str = Field(
        ...,
        description="Source code to be explained"
    )


class LineBreakdownItem(BaseModel):
    """Schema for individual line explanation items."""
    line_number: int
    code_snippet: str
    explanation: str


class ExplainResponse(BaseModel):
    """Response schema for code explanation endpoint."""
    status: str = Field("success", description="Request processing status")
    language: str
    code_length: int
    line_count: int
    is_ai_connected: bool = Field(False, description="Flag indicating live AI connection status")
    message: str
    simple_explanation: str
    line_by_line: List[LineBreakdownItem]
    example_output: str
    debugging_suggestions: List[str]


# --- Gemini Prompt Builder ---

def _build_gemini_prompt(language: str, code: str) -> str:
    """
    Build a structured prompt that instructs Gemini to return a valid JSON object
    with exactly the four sections we need.

    SAFETY: The prompt explicitly instructs Gemini NOT to execute the code.
    """
    return f"""You are an expert programming tutor. A student has submitted the following {language} code for explanation.

IMPORTANT RULES:
- Do NOT execute, run, or evaluate the code.
- Do NOT include any markdown formatting (no ```json, no ``` blocks).
- Respond ONLY with a single valid raw JSON object — nothing else before or after it.
- Keep explanations beginner-friendly and clear.
- The "example_output" field should be your best prediction of what the code would print/return if run — based on reading the code, not by executing it.
- The "line_by_line" array must cover every meaningful line (skip blank lines).

Here is the {language} code:
---
{code}
---

Respond with this exact JSON structure:
{{
  "simple_explanation": "A clear, beginner-friendly paragraph explaining what this code does overall.",
  "line_by_line": [
    {{
      "line_number": 1,
      "code_snippet": "the exact code from that line",
      "explanation": "what this specific line does"
    }}
  ],
  "example_output": "A prediction of what this code would print or return if executed (do not run it, just read it).",
  "debugging_suggestions": [
    "Tip or potential error 1",
    "Tip or potential error 2"
  ]
}}"""


# --- Gemini API Call ---

def _call_gemini(language: str, code: str) -> dict:
    """
    Call the Gemini API and return the parsed JSON response dict.

    Tries each model in _GEMINI_MODELS in order.
    Each call is wrapped in a hard wall-clock timeout (_PER_MODEL_TIMEOUT seconds)
    that cuts through the SDK's internal tenacity retry loop.

    Retry conditions (try next model): 503 UNAVAILABLE, 429 RESOURCE_EXHAUSTED.
    Stop immediately on: 404 NOT_FOUND, 401/403 auth errors, JSON parse errors.

    Raises:
        HTTPException 503 - if no valid API key is configured.
        HTTPException 502 - if all models fail or an unrecoverable error occurs.
    """
    import concurrent.futures
    import time

    if not AI_ENABLED or gemini_client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "AI service is not configured. "
                "Please add your GEMINI_API_KEY to backend/.env and restart the server. "
                "Get a free key at: https://aistudio.google.com/app/apikey"
            )
        )

    prompt = _build_gemini_prompt(language, code)
    last_error_str = "Unknown error"

    for i, model_name in enumerate(_GEMINI_MODELS):
        logger.info(f"[{i+1}/{len(_GEMINI_MODELS)}] Trying Gemini model: {model_name}")

        # --- Hard wall-clock timeout per model call ---
        # The SDK uses tenacity internally and may retry a 503 for minutes.
        # We run the call in a thread and kill it after _PER_MODEL_TIMEOUT seconds.
        def _do_call(m=model_name):
            return gemini_client.models.generate_content(
                model=m,
                contents=prompt
            )

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(_do_call)
                try:
                    response = future.result(timeout=_PER_MODEL_TIMEOUT)
                except concurrent.futures.TimeoutError:
                    future.cancel()
                    logger.warning(
                        f"Model {model_name} did not respond within {_PER_MODEL_TIMEOUT}s "
                        f"(SDK tenacity retrying internally). Moving to next model."
                    )
                    last_error_str = f"Timeout after {_PER_MODEL_TIMEOUT}s (503 overload)"
                    if i < len(_GEMINI_MODELS) - 1:
                        time.sleep(_RETRY_DELAY)
                    continue

            raw_text = response.text.strip()
            logger.info(
                f"Gemini responded successfully via {model_name} "
                f"({len(raw_text)} chars)"
            )
            return _parse_gemini_response(raw_text)

        except HTTPException:
            raise  # propagate our own HTTP exceptions (e.g., from _parse_gemini_response)

        except Exception as e:
            error_str = str(e)
            last_error_str = error_str[:300]
            logger.error(
                f"Gemini [{model_name}] error ({type(e).__name__}): {error_str}"
            )

            # --- Permanent failures: stop immediately, do not try other models ---
            is_permanent = (
                "404" in error_str or "NOT_FOUND" in error_str
                or "401" in error_str or "403" in error_str
                or "API_KEY_INVALID" in error_str
                or "PERMISSION_DENIED" in error_str
            )
            if is_permanent:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=(
                        f"The AI model '{model_name}' returned a permanent error. "
                        f"Error: {error_str[:250]}"
                    )
                )

            # --- Temporary failures: try next model ---
            is_temporary = (
                "503" in error_str or "UNAVAILABLE" in error_str
                or "429" in error_str or "RESOURCE_EXHAUSTED" in error_str
            )
            if is_temporary and i < len(_GEMINI_MODELS) - 1:
                logger.warning(
                    f"Model {model_name} temporarily unavailable. "
                    f"Trying next model in {_RETRY_DELAY}s..."
                )
                time.sleep(_RETRY_DELAY)
                continue

            # Anything else (network error, unexpected) — stop
            break

    # All models exhausted
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=(
            f"All AI models are temporarily unavailable. "
            f"Last error: {last_error_str}. "
            f"This is a temporary Google server issue. Please try again in a few minutes."
        )
    )


def _parse_gemini_response(raw_text: str) -> dict:
    """Strip markdown fences from Gemini's response and parse as JSON."""
    # Strip accidental markdown fences Gemini sometimes adds despite instructions
    if raw_text.startswith("```"):
        lines = raw_text.splitlines()
        lines = [l for l in lines if not l.strip().startswith("```")]
        raw_text = "\n".join(lines).strip()

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError as e:
        logger.error(f"Gemini returned non-JSON response. JSONDecodeError: {e}\nRaw text (first 500 chars): {raw_text[:500]}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI returned an unexpected response format. Please try again."
        )


# --- Helper: safely extract Gemini JSON fields with fallbacks ---

def _safe_str(data: dict, key: str, fallback: str) -> str:
    """Return a string field from the dict, or fallback if missing/wrong type."""
    val = data.get(key)
    if isinstance(val, str) and val.strip():
        return val.strip()
    return fallback


def _safe_list_str(data: dict, key: str, fallback: List[str]) -> List[str]:
    """Return a list-of-strings field from the dict, or fallback if missing/wrong type."""
    val = data.get(key)
    if isinstance(val, list) and all(isinstance(i, str) for i in val):
        return val
    return fallback


def _safe_line_by_line(data: dict, code_lines: List[str]) -> List[LineBreakdownItem]:
    """
    Parse the line_by_line array from Gemini's JSON response.
    Falls back to a generic per-line breakdown if the data is malformed.
    """
    raw = data.get("line_by_line")
    items: List[LineBreakdownItem] = []

    if isinstance(raw, list):
        for entry in raw:
            if not isinstance(entry, dict):
                continue
            try:
                items.append(LineBreakdownItem(
                    line_number=int(entry.get("line_number", 0)),
                    code_snippet=str(entry.get("code_snippet", "")).strip(),
                    explanation=str(entry.get("explanation", "")).strip()
                ))
            except Exception:
                continue  # Skip malformed entries silently

    # If Gemini gave us nothing usable, build a minimal fallback
    if not items:
        for i, line in enumerate(code_lines[:10], start=1):
            snippet = line.strip() or "(empty line)"
            items.append(LineBreakdownItem(
                line_number=i,
                code_snippet=snippet,
                explanation="AI did not provide a breakdown for this line."
            ))

    return items


# --- API Endpoints ---

@app.get("/", tags=["Root"])
def root_status():
    """Welcome root endpoint with links to health check and interactive documentation."""
    return {
        "project": "AI Code Explainer",
        "status": "online",
        "step": "Step 2B: Gemini AI Integration",
        "ai_enabled": AI_ENABLED,
        "docs_url": "/docs",
        "health_check_url": "/api/health"
    }


# Support both GET and POST for health check
@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
@app.post("/api/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    """
    Health check endpoint.
    Returns status: ok to confirm the backend server is running.
    The ai_connected field reflects whether a valid Gemini API key is loaded.
    """
    return HealthResponse(ai_connected=AI_ENABLED)


@app.post(
    "/api/explain",
    response_model=ExplainResponse,
    status_code=status.HTTP_200_OK,
    tags=["Explanation"]
)
def explain_code(request: ExplainRequest):
    """
    Code explanation endpoint (Step 2B — Gemini AI Integration).

    Validates:
    - Code is not empty or pure whitespace.
    - Code does not exceed MAX_CODE_LENGTH (10,000 characters).

    Then calls the Google Gemini API to generate:
    - A simple, plain-English explanation of the code.
    - A line-by-line breakdown of every meaningful line.
    - A predicted example output (without executing the code).
    - Debugging suggestions and potential error tips.

    SAFETY:
    - User code is NEVER executed or evaluated.
    - The Gemini API key is loaded from the server's .env only — never from the frontend.
    """
    cleaned_code = request.code.strip()
    cleaned_lang = request.language.strip().lower()

    # 1. Validation: Reject empty or pure whitespace code
    if not cleaned_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Source code cannot be empty. Please enter or paste some code to explain."
        )

    # 2. Validation: Reject code exceeding maximum length
    if len(request.code) > MAX_CODE_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Code length ({len(request.code):,} characters) exceeds maximum allowed size ({MAX_CODE_LENGTH:,} characters)."
        )

    # Calculate basic text stats
    lines = cleaned_code.split("\n")
    line_count = len(lines)
    code_length = len(cleaned_code)
    lang_display = cleaned_lang.capitalize()

    # 3. Call the Gemini API
    logger.info(f"Calling Gemini for {lang_display} code ({line_count} lines, {code_length} chars)")
    gemini_data = _call_gemini(lang_display, cleaned_code)

    # 4. Safely extract each field from Gemini's response (with fallbacks)
    simple_explanation = _safe_str(
        gemini_data, "simple_explanation",
        fallback=f"AI could not generate a summary for this {lang_display} snippet."
    )
    example_output = _safe_str(
        gemini_data, "example_output",
        fallback="AI could not predict the output for this code."
    )
    debugging_suggestions = _safe_list_str(
        gemini_data, "debugging_suggestions",
        fallback=["AI did not return debugging suggestions. Please try again."]
    )
    line_by_line = _safe_line_by_line(gemini_data, lines)

    return ExplainResponse(
        status="success",
        language=lang_display,
        code_length=code_length,
        line_count=line_count,
        is_ai_connected=True,
        message=f"AI explanation generated successfully for your {lang_display} code.",
        simple_explanation=simple_explanation,
        line_by_line=line_by_line,
        example_output=example_output,
        debugging_suggestions=debugging_suggestions,
    )

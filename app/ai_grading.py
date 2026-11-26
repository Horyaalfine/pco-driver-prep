"""AI feedback for ELR speaking practice: transcribe a learner's recorded
answer, then grade it against a rubric, via the OpenAI API.

Two plain HTTP calls (no SDK dependency — see requirements.txt) rather than
anything fancier: this is a low-volume, non-critical-path feature, and a
direct `requests` call is easier to reason about and keeps the dependency
footprint small.

Both model names are configurable (OPENAI_TRANSCRIBE_MODEL,
OPENAI_GRADING_MODEL) because OpenAI periodically retires models — e.g.
whisper-1 and gpt-4o-mini-transcribe are both scheduled for shutdown in Feb
2027 — so swapping the replacement in is an env var change, not a deploy.

Every function here returns either a plain result or raises GradingError
with a message that's safe to show the user directly (never a raw
API/network error, which could leak request details).
"""

import json

import requests

OPENAI_API_BASE = "https://api.openai.com/v1"
REQUEST_TIMEOUT_SECONDS = 30

GRADING_SYSTEM_PROMPT = (
    "You are an examiner-style English language coach helping a candidate "
    "prepare for TfL's private hire driver English Language Requirement "
    "(ELR) speaking interview. You will be given the interview question "
    "and a transcript of the candidate's spoken answer. Assess it on "
    "clarity, grammar, fluency of expression, and whether it actually "
    "answers the question asked. Be encouraging but honest — point out "
    "specific mistakes with a brief example of the correction, not vague "
    "praise. Keep feedback to 3-5 short sentences. "
    'Respond with ONLY a JSON object of the exact form: '
    '{"score": <integer 0-100>, "feedback": "<your feedback>"}. '
    "No other text before or after the JSON."
)


class GradingError(Exception):
    """Raised with a message that is safe to show directly to the user."""


def _require_api_key(api_key: str) -> None:
    if not api_key:
        raise GradingError(
            "AI feedback isn't set up yet on this server — ask the site admin to add an API key."
        )


def transcribe_audio(api_key: str, model: str, audio_bytes: bytes, filename: str) -> str:
    """Transcribe a recorded answer. Returns the transcript text."""
    _require_api_key(api_key)
    if not audio_bytes:
        raise GradingError("No audio was received — please record an answer first.")

    try:
        response = requests.post(
            f"{OPENAI_API_BASE}/audio/transcriptions",
            headers={"Authorization": f"Bearer {api_key}"},
            data={"model": model},
            files={"file": (filename or "recording.webm", audio_bytes, "audio/webm")},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except requests.RequestException:
        raise GradingError("Couldn't reach the transcription service — please try again in a moment.")

    if response.status_code != 200:
        raise GradingError("The transcription service couldn't process that recording — please try again.")

    try:
        text = response.json().get("text", "").strip()
    except ValueError:
        raise GradingError("The transcription service returned an unexpected response.")

    if not text:
        raise GradingError("No speech was detected in that recording — please try again, speaking clearly.")

    return text


def synthesize_speech(api_key: str, model: str, voice: str, text: str) -> bytes:
    """Read a speaking prompt's question aloud (examiner-style), so practice
    matches the real interview's listen-then-speak format. Returns raw MP3
    bytes — callers (see the /question-audio route in app/learning.py) are
    expected to cache the result, since the input text never changes."""
    _require_api_key(api_key)

    try:
        response = requests.post(
            f"{OPENAI_API_BASE}/audio/speech",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={"model": model, "voice": voice, "input": text},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except requests.RequestException:
        raise GradingError("Couldn't reach the text-to-speech service — please try again in a moment.")

    if response.status_code != 200 or not response.content:
        raise GradingError("The text-to-speech service couldn't read that question — please try again.")

    return response.content


def grade_transcript(api_key: str, model: str, question: str, transcript: str) -> dict:
    """Grade a transcript against the rubric. Returns {"score": int, "feedback": str}."""
    _require_api_key(api_key)

    user_content = f"Interview question: {question}\n\nCandidate's spoken answer (transcript): {transcript}"

    try:
        response = requests.post(
            f"{OPENAI_API_BASE}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": GRADING_SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
                "temperature": 0.3,
                "response_format": {"type": "json_object"},
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except requests.RequestException:
        raise GradingError("Couldn't reach the feedback service — please try again in a moment.")

    if response.status_code != 200:
        raise GradingError("The feedback service couldn't grade that answer — please try again.")

    try:
        content = response.json()["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        score = int(parsed["score"])
        feedback = str(parsed["feedback"]).strip()
    except (KeyError, ValueError, IndexError, TypeError):
        raise GradingError("The feedback service returned an unexpected response — please try again.")

    score = max(0, min(100, score))
    if not feedback:
        raise GradingError("The feedback service returned an unexpected response — please try again.")

    return {"score": score, "feedback": feedback}

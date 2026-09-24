"""Pluggable LLM backend.

Three ways to run this project, chosen with KUBAKA_BACKEND:

  claude_cli  (default, free)  Claude Code subscription via `claude -p`.
                               Needs: npm i -g @anthropic-ai/claude-code && claude login
  gemini      (free tier)      Google AI Studio key, no credit card.
                               Needs: pip install google-genai, GOOGLE_API_KEY in .env
  anthropic   (paid)           Anthropic API key in ANTHROPIC_API_KEY.

Every backend exposes the same call: complete(prompt) -> str
"""
import os
import shutil
import subprocess

from .config import BACKEND, ANTHROPIC_API_KEY, GOOGLE_API_KEY, GEMINI_MODEL, CLAUDE_CLI_MODEL

_gemini_client = None
_anthropic_client = None


class BackendError(RuntimeError):
    pass


def _complete_claude_cli(prompt, max_tokens=None):
    exe = shutil.which("claude")
    if not exe:
        raise BackendError(
            "`claude` not on PATH. Install with:\n"
            "  npm install -g @anthropic-ai/claude-code\n"
            "then run:  claude login"
        )
    proc = subprocess.run(
        [exe, "-p", prompt, "--model", CLAUDE_CLI_MODEL],
        capture_output=True, text=True, timeout=300,
        stdin=subprocess.DEVNULL,
    )
    out = (proc.stdout or "").strip()
    if proc.returncode != 0 or not out:
        err = (proc.stderr or out or "no output").strip()
        if "authenticate" in err.lower() or "oauth" in err.lower():
            raise BackendError("Claude CLI is not logged in. Run:  claude login")
        raise BackendError(f"claude CLI failed: {err[:300]}")
    return out


def _complete_gemini(prompt, max_tokens=None):
    global _gemini_client
    if not GOOGLE_API_KEY:
        raise BackendError("GOOGLE_API_KEY not set. Get a free key at aistudio.google.com/apikey")
    if _gemini_client is None:
        try:
            from google import genai
        except ImportError as exc:
            raise BackendError("pip install google-genai") from exc
        _gemini_client = genai.Client(api_key=GOOGLE_API_KEY)
    resp = _gemini_client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    text = (getattr(resp, "text", None) or "").strip()
    if not text:
        raise BackendError("Gemini returned an empty response")
    return text


def _complete_anthropic(prompt, max_tokens=1500):
    global _anthropic_client
    if not ANTHROPIC_API_KEY:
        raise BackendError("ANTHROPIC_API_KEY not set")
    if _anthropic_client is None:
        import anthropic
        _anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    msg = _anthropic_client.messages.create(
        model="claude-sonnet-5", max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text.strip()


_BACKENDS = {
    "claude_cli": _complete_claude_cli,
    "gemini": _complete_gemini,
    "anthropic": _complete_anthropic,
}


def complete(prompt, max_tokens=1500):
    """Run a prompt on the configured backend.

    max_tokens is honoured by the anthropic backend; the claude_cli and
    gemini backends use their own defaults and ignore it.
    """
    fn = _BACKENDS.get(BACKEND)
    if fn is None:
        raise BackendError(f"Unknown KUBAKA_BACKEND={BACKEND!r}. Options: {', '.join(_BACKENDS)}")
    return fn(prompt, max_tokens=max_tokens)


def which_backend():
    return BACKEND


def health():
    """Cheap check that the configured backend actually answers."""
    try:
        out = complete('Reply with exactly: OK')
        return True, f"{BACKEND}: {out[:60]}"
    except Exception as exc:
        return False, f"{BACKEND}: {exc}"

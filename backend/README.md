# VetScribe Backend (reference implementation)

A minimal reference server that satisfies the HTTP contract VetScribe's `ApiClient` expects
(`POST /api/soap` with raw WAV bytes, returns JSON with `subjective`/`objective`/`assessment`/`plan`).
It's a separate project from the desktop tray app — this is meant to run on a server (or locally for
development), not ship inside the Windows installer.

Transcription and SOAP-note generation are each behind a small interface, selected independently, so
you can mix providers (e.g. Gemini for transcription, Anthropic for note generation):

| Env var | Values | Default |
|---|---|---|
| `VETSCRIBE_TRANSCRIPTION_PROVIDER` | `openai`, `gemini` | `openai` |
| `VETSCRIBE_NOTE_PROVIDER` | `openai`, `anthropic`, `gemini` | `openai` |

Provider credentials (only the ones for your selected providers are required):

| Env var | Purpose |
|---|---|
| `OPENAI_API_KEY` | OpenAI Whisper transcription and/or GPT note generation |
| `ANTHROPIC_API_KEY` | Claude note generation |
| `GEMINI_API_KEY` | Gemini transcription and/or note generation |
| `OPENAI_TRANSCRIPTION_MODEL` | default `whisper-1` |
| `OPENAI_NOTE_MODEL` | default `gpt-4o-mini` |
| `ANTHROPIC_NOTE_MODEL` | default `claude-sonnet-4-5` |
| `GEMINI_TRANSCRIPTION_MODEL` | default `gemini-2.0-flash` |
| `GEMINI_NOTE_MODEL` | default `gemini-2.0-flash` |

`VETSCRIBE_BACKEND_API_KEY` is a separate shared secret (distinct from the provider keys above): if
set, incoming requests must send `Authorization: Bearer <that value>` — this is the value you'd put in
VetScribe's own "API Key" setting. If unset, the backend accepts unauthenticated requests.

The SOAP-note system prompt sent to whichever note-generation provider is selected lives in
`src/vetscribe_backend/prompts.py` (`SOAP_SYSTEM_PROMPT`) — edit it there if you want to change the
clinical instructions given to the model.

## Running

```bash
cd backend
uv sync
VETSCRIBE_NOTE_PROVIDER=anthropic ANTHROPIC_API_KEY=sk-ant-... \
VETSCRIBE_TRANSCRIPTION_PROVIDER=openai OPENAI_API_KEY=sk-... \
  uv run python -m vetscribe_backend.main
```

Listens on port 8443 by default (override with `PORT`), matching VetScribe's default
`api_endpoint` of `https://localhost:8443/api/soap` — note this runs plain HTTP, so for local dev
point VetScribe's Settings at `http://localhost:8443/api/soap`, or put a TLS-terminating proxy in
front of it for anything beyond local testing.

## Testing

```bash
cd backend
uv run pytest -v
```

All provider HTTP calls are mocked with `respx` in tests — no real API keys or network calls are
needed to run the suite.

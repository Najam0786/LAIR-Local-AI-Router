# Getting Started with LAIR

This is a practical, step-by-step guide to running LAIR on your own machine —
what to install, how to start it, and how to connect a chat client to it.
For the project's vision and architecture, see [README.md](README.md) and
[docs/index.md](docs/index.md).

---

## What you get by the end of this guide

One command starts LAIR. From then on, when you ask it something, it:

1. Figures out what kind of task the prompt is (coding, reasoning, vision,
   general chat, ...) and how complex it is.
2. Picks the best available local model for that task — accounting for
   your hardware, quantization, KV-cache footprint, and (optionally)
   language and battery state.
3. Makes sure LM Studio's server is running and that model is loaded —
   automatically, with no manual "start server" / "load model" steps.
4. Runs the request and returns an OpenAI-compatible response, with an
   explanation of why that model was picked and an estimate of the
   cloud cost you avoided.

This has been built and verified end-to-end with **LM Studio** as the model
backend and **Continue** (the VS Code extension) as the chat client. Any
other OpenAI-compatible client will work the same way, since LAIR exposes a
standard `/v1/chat/completions` endpoint.

---

## Prerequisites

- **Python 3.13+**
- **[LM Studio](https://lmstudio.ai/)** installed, with at least one model
  downloaded (via LM Studio's own model search/download UI).
- **Git**, to clone the repository.
- A chat client that can talk to a custom OpenAI-compatible endpoint —
  this guide covers **Continue**, but anything works (Cursor, Cline, a
  simple `curl`, your own script, etc).

---

## 1. Clone and install

```bash
git clone https://github.com/Najam0786/LAIR-Local-AI-Router.git
cd LAIR-Local-AI-Router

python -m venv .venv
```

Activate the virtual environment:

```powershell
# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
```

```bash
# macOS / Linux
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Optional: if you want the local voice interface (speech in, speech out),
also install its extra dependencies — see [Voice interface](#voice-interface-optional) below:

```bash
pip install -r requirements-voice.txt
```

---

## 2. Profile your machine

```bash
python -m lair doctor --init
```

This reads your machine's RAM, GPU, and SSD speed, tells you which
hardware tier LAIR thinks you're in (`entry` / `standard` / `enthusiast` /
`cpu_only`), and recommends a model portfolio sized for it. `--init` saves
that recommendation to `configs/active_portfolio.yaml` — some routing
features (community benchmark fallback, streaming-aware routing) read this
file to know your machine's tier, so it's worth running once even if you
don't use every model it suggests. **LAIR never downloads models for you**
— it prints search terms for LM Studio's own model catalog.

---

## 3. Open LM Studio

Just open the LM Studio app and leave it running (the system tray is fine —
it doesn't need to stay in the foreground). Make sure you've downloaded at
least one model inside it.

You do **not** need to manually start LM Studio's local server or load a
model yourself — LAIR handles both of those automatically per-request (see
[How the auto-start works](#how-the-auto-start-works) below). LM Studio
itself, however, does need to be open; LAIR can recover a stopped server or
an unloaded model, but it cannot launch LM Studio from a fully closed state.

---

## 4. Run LAIR

One command, from the repository root, with the virtual environment active:

```bash
uvicorn main:app --reload
```

You should see:

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

That's it — LAIR is up on `http://127.0.0.1:8000`.

---

## 5. Verify it's working

```bash
curl http://127.0.0.1:8000/health
```

```json
{"status":"healthy","application":"LAIR","version":"0.3.0-alpha"}
```

You can also open `http://127.0.0.1:8000/docs` in a browser for the full
interactive API reference (Swagger UI), or try a chat request directly:

```bash
curl -X POST http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"say hi"}]}'
```

The first request after LM Studio has been idle can take anywhere from a
few seconds to about a minute — that's LAIR loading the right model into
LM Studio behind the scenes. Every request after that is fast.

---

## 6. Connect a client

### One command (recommended)

```bash
python -m lair install --client continue
```

This writes (and backs up the original of) Continue's config file so it
points at LAIR automatically. Run `python -m lair install` with no
arguments to auto-detect installed clients. `--uninstall` restores the
backup.

### Continue (VS Code extension) — manual setup

Open Continue's config file (`~/.continue/config.yaml`) and add LAIR as a
custom OpenAI-compatible model:

```yaml
models:
  - name: LAIR (Auto-routed)
    provider: openai
    model: lair-routed
    apiBase: http://localhost:8000/v1/
    defaultCompletionOptions:
      stream: false
      maxTokens: 1024
```

Reload the VS Code window (`Ctrl+Shift+P` → "Developer: Reload Window") if
Continue doesn't pick up the change immediately. Select **LAIR
(Auto-routed)** from Continue's model picker and start chatting — LAIR
decides which underlying model actually answers.

### Any other OpenAI-compatible client

Point its base URL at:

```
http://localhost:8000/v1/
```

The `model` field in requests is accepted for compatibility but ignored —
LAIR's routing engine decides which model actually handles the request.

---

## How the auto-start works

LAIR uses LM Studio's own CLI (`lms`, installed automatically alongside LM
Studio and added to your `PATH`) to manage things headlessly:

- Before answering a request, LAIR checks whether LM Studio's local server
  is reachable. If not, it runs `lms server start`.
- It then checks whether the model it needs is loaded. If not, it runs
  `lms load <model> -y`.
- Models can auto-unload themselves after being idle (LM Studio's own TTL
  setting, tuned per-model by LAIR's scheduler) — LAIR re-checks and
  reloads as needed on the next request, so you never have to do this by
  hand.

This can be turned off if you'd rather manage LM Studio yourself — see
[Configuration](#configuration).

**Known limitation:** this only recovers a *stopped server* or *unloaded
model* while LM Studio itself is open. If you fully quit the LM Studio
application (not just its server), LAIR cannot relaunch it — reopen LM
Studio manually in that case.

---

## Documents (RAG-lite)

Ingest a document, then reference it in a chat request:

```bash
curl -X POST http://127.0.0.1:8000/v1/lair/documents -F "file=@manual.pdf"
# -> {"document_id": "...", "filename": "manual.pdf", "chunk_count": 42}

curl -X POST http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"What does section 3 say?"}], "lair_document_id":"<document_id>"}'
```

The chunks most relevant to your question are retrieved locally (via
`fastembed`, no cloud call) and injected before the model sees your
question. `GET /v1/lair/documents` lists ingested documents;
`DELETE /v1/lair/documents/{id}` removes one.

---

## Project memory

Off by default (`ENABLE_PROJECT_MEMORY=false`) — the most privacy-sensitive
feature LAIR has, since it durably stores things you say. Turn it on, then
tag requests with a project scope:

```bash
curl -X POST http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Remember that I prefer tabs, not spaces."}], "lair_project_scope":"my-project"}'
```

Manage what's stored:

```bash
python -m lair memory list my-project
python -m lair memory show <memory_id>
python -m lair memory forget <memory_id>
python -m lair memory forget my-project --scope   # wipe an entire scope
python -m lair memory export my-project
```

Everything is local, JSON-backed, and fully yours to inspect or delete.

---

## Voice interface (optional)

Ships as an optional extra (`pip install -r requirements-voice.txt`) so the
core install stays light. Once installed:

```bash
curl -X POST http://127.0.0.1:8000/v1/audio/transcriptions -F "file=@question.wav"
curl -X POST http://127.0.0.1:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"input":"Here is your answer."}' --output reply.wav
```

Text-to-speech additionally needs a local Kokoro model file pair
(`VOICE_TTS_MODEL_PATH` / `VOICE_TTS_VOICES_PATH` below) — Kokoro doesn't
auto-download its weights the way the embedding model does. A full
round trip (transcribe → route → synthesize) against a running server:

```bash
python -m lair voice --input question.wav --output reply.wav
```

Without the extra installed, or without the TTS model files configured,
these endpoints return a `503` with an actionable message — never a crash.

---

## Cloud escalation (optional)

Off by default. When enabled with a nonzero monthly budget, a genuinely
hard request (high complexity, low local-routing confidence) can escalate
to a configured OpenAI-compatible cloud endpoint instead of settling for
the best-available local answer. Every cloud-routed response is marked
`lair_meta.routed_to_cloud=true` with a reason — never silent. See
`docs/rfcs/RFC-0001-hybrid-cloud-escalation.md` for the full design and
safeguards.

---

## Configuration

All settings are optional environment variables (put them in a `.env` file
at the repository root, or export them directly). This is a curated subset
covering the most commonly adjusted ones — see `app/core/settings.py` for
the complete, authoritative list (every feature above has its own
`ENABLE_*` toggle, off by default wherever privacy, cost, or correctness
risk warrants it).

| Variable | Default | Purpose |
|---|---|---|
| `HOST` | `127.0.0.1` | Address LAIR binds to |
| `PORT` | `8000` | Port LAIR binds to |
| `LM_STUDIO_URL` | `http://localhost:1234/v1` | Where LM Studio's API lives |
| `ENABLE_LM_STUDIO_AUTOSTART` | `true` | Auto-manage LM Studio's server/model as described above |
| `LMS_CLI_PATH` | `lms` | Path to the LM Studio CLI, if not on `PATH` |
| `REQUEST_TIMEOUT` | `300` | Max seconds to wait on a completion request |
| `ENABLE_RESPONSE_CACHE` | `false` | Serve repeated identical requests from cache |
| `ENABLE_CLOUD_ESCALATION` | `false` | Allow budget-capped cloud escalation (see above) |
| `CLOUD_MONTHLY_BUDGET_USD` | `0.0` | Hard cap on real cloud spend per month |
| `ENABLE_PROJECT_MEMORY` | `false` | Persistent per-project local memory (see above) |
| `ENABLE_STREAMING_ROUTING` | `false` | Offer oversized-but-streamable models as a last-resort, explained pick (infrastructure only — see ROADMAP.md Phase 4) |
| `VOICE_TTS_MODEL_PATH` / `VOICE_TTS_VOICES_PATH` | `""` | Local Kokoro model files for text-to-speech |

---

## Troubleshooting

**"Connection error" from your chat client, but LAIR looks fine in its own
terminal** — double check the client's configured port/URL matches what
LAIR actually printed on startup (`http://127.0.0.1:8000`). This is the
single most common cause.

**`503 No AI models are currently available`** — LM Studio itself isn't
running. Reopen the LM Studio application; LAIR will take it from there.

**`503` from `/v1/audio/transcriptions` or `/v1/audio/speech`** — the
optional voice extra isn't installed (`pip install -r requirements-voice.txt`),
or (for speech synthesis) `VOICE_TTS_MODEL_PATH`/`VOICE_TTS_VOICES_PATH`
aren't configured. The error message says which.

**A request seems to hang for a while, then succeeds** — expected on a
cold start, while LAIR waits for LM Studio to start its server and/or load
a multi-gigabyte model. Subsequent requests are fast.

**Project memory doesn't seem to do anything** — check `ENABLE_PROJECT_MEMORY`
is `true` and that `lair_project_scope` is set on your request; memory is
also only extracted from messages matching a durable-statement pattern
("remember...", "I prefer...", "always/never...") — an ordinary question
won't create a memory, by design.

---

## What's actually implemented today

LAIR is alpha software (`v0.3.0-alpha`), but every feature listed here is
real, tested, and merged — see [README.md](README.md)'s "What's Actually
Working Today" section for the complete, current list, and `CHANGELOG.md`
for the dated history of each one.

See [ROADMAP.md](ROADMAP.md) for what's planned next, and
[docs/index.md](docs/index.md) for the full architecture and design
rationale behind all of it.

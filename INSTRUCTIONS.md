# Getting Started with LAIR

This is a practical, step-by-step guide to running LAIR on your own machine —
what to install, how to start it, and how to connect a chat client to it.
For the project's vision and architecture, see [README.md](README.md) and
[docs/index.md](docs/index.md).

---

## What you get by the end of this guide

One command starts LAIR. From then on, when you ask it something, it:

1. Figures out what kind of task the prompt is (coding, reasoning, vision,
   general chat, ...).
2. Picks the best available local model for that task.
3. Makes sure LM Studio's server is running and that model is loaded —
   automatically, with no manual "start server" / "load model" steps.
4. Runs the request and returns an OpenAI-compatible response.

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

---

## 2. Open LM Studio

Just open the LM Studio app and leave it running (the system tray is fine —
it doesn't need to stay in the foreground). Make sure you've downloaded at
least one model inside it.

You do **not** need to manually start LM Studio's local server or load a
model yourself — LAIR handles both of those automatically per-request (see
[How the auto-start works](#how-the-auto-start-works) below). LM Studio
itself, however, does need to be open; LAIR can recover a stopped server or
an unloaded model, but it cannot launch LM Studio from a fully closed state.

---

## 3. Run LAIR

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

## 4. Verify it's working

```bash
curl http://127.0.0.1:8000/health
```

```json
{"status":"healthy","application":"LAIR","version":"0.2.0-alpha"}
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

## 5. Connect a client

### Continue (VS Code extension) — verified setup

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
  setting) — LAIR re-checks and reloads as needed on the next request, so
  you never have to do this by hand.

This can be turned off if you'd rather manage LM Studio yourself — see
[Configuration](#configuration).

**Known limitation:** this only recovers a *stopped server* or *unloaded
model* while LM Studio itself is open. If you fully quit the LM Studio
application (not just its server), LAIR cannot relaunch it — reopen LM
Studio manually in that case.

---

## Configuration

All settings are optional environment variables (put them in a `.env` file
at the repository root, or export them directly). Defaults shown below.

| Variable | Default | Purpose |
|---|---|---|
| `HOST` | `127.0.0.1` | Address LAIR binds to |
| `PORT` | `8000` | Port LAIR binds to |
| `LM_STUDIO_URL` | `http://localhost:1234/v1` | Where LM Studio's API lives |
| `ENABLE_LM_STUDIO_AUTOSTART` | `true` | Auto-manage LM Studio's server/model as described above |
| `LMS_CLI_PATH` | `lms` | Path to the LM Studio CLI, if not on `PATH` |
| `REQUEST_TIMEOUT` | `300` | Max seconds to wait on a completion request |

---

## Troubleshooting

**"Connection error" from your chat client, but LAIR looks fine in its own
terminal** — double check the client's configured port/URL matches what
LAIR actually printed on startup (`http://127.0.0.1:8000`). This is the
single most common cause.

**`503 No AI models are currently available`** — LM Studio itself isn't
running. Reopen the LM Studio application; LAIR will take it from there.

**A request seems to hang for a while, then succeeds** — expected on a
cold start, while LAIR waits for LM Studio to start its server and/or load
a multi-gigabyte model. Subsequent requests are fast.

---

## What's actually implemented today

LAIR is alpha software (`v0.2.0-alpha`). What's real and working right now:

- Capability-aware request analysis (coding / reasoning / vision /
  summarization / translation / general text).
- Benchmark-informed, explainable model scoring and selection.
- OpenAI-compatible `/v1/chat/completions` and `/v1/models`, including
  streaming.
- Automatic LM Studio server/model lifecycle management (this guide).
- A local knowledge base of past routing decisions and outcomes.

See [ROADMAP.md](ROADMAP.md) for what's planned next, and
[docs/index.md](docs/index.md) for the full architecture and design
rationale behind all of it.

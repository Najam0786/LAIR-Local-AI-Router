# LAIR Web

A local-first chat client for LAIR: streaming chat, voice in/out, document
drag-and-drop, conversation history, and a live routing panel that shows
exactly how each request was scored (candidates, per-factor provenance,
confidence).

Talks directly to LAIR's existing API (`/v1/chat/completions`,
`/v1/audio/*`, `/v1/lair/documents`, `/route`) -- no separate backend of
its own. Conversation history is stored only in the browser; LAIR's
server stays stateless.

## Running

Start the LAIR backend first (from the repo root):

```bash
uvicorn main:app --reload
```

Then, from this directory:

```bash
npm install
npm run dev
```

Open the URL Vite prints (typically `http://localhost:5173`). The dev
server proxies `/v1`, `/route`, `/models`, `/health`, and `/benchmarks`
to `http://127.0.0.1:8000`, so no CORS configuration is needed.

## Build

```bash
npm run build
```

Outputs to `dist/`, servable as static files by anything (or by LAIR
itself, if later mounted as a static directory).

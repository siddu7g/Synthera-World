# Project Decisions

## Current architecture
- FastAPI backend on `localhost:8765`
- React frontend on `localhost:3000`
- Generated simulation artifacts are persisted with `generation_id`

## Session memory
- Chat endpoint stores short rolling memory per `session_id`
- Frontend keeps a default `session_id` and sends it with each chat request

## Cost strategy
- Use deterministic templates for repeatable demo flows
- Use LLM generation for open-ended requests

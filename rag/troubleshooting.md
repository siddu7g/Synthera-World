# Troubleshooting Notes

## Uvicorn starts in wrong Python
- Symptom: `ModuleNotFoundError: sqlmodel`
- Fix: activate `synthera-py310`, run `python -m uvicorn main:app --reload --port 8765`

## Isaac script import errors
- Symptom: runtime `ImportError` for hallucinated APIs
- Fix: prefer deterministic template paths for demos and keep validator guards strict

## Conda warning from Isaac
- Symptom: warning about running inside conda env
- Status: warning only; simulation can still run

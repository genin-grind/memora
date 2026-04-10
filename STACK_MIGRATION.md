# Memora Stack Migration

This repo now contains the first foundation for a staged migration away from Streamlit.

## Apps

- `frontend/`: React + Vite shell for the new demo UI
- `backend/`: Express API for frontend-facing routes
- `python_service/`: FastAPI service that will gradually absorb the current Python business logic

## Initial Build Strategy

We are keeping the current Streamlit app working while rebuilding the product in vertical slices:

1. Login and protected shell
2. Main Memora query flow
3. Source Explorer
4. Organization dashboard
5. Sync and control center

## Run Plan

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Backend

```bash
cd backend
npm install
npm run dev
```

### Python Service

```bash
cd python_service
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Current State

- The new app shells and routes are scaffolded.
- The Streamlit app remains the source of truth for live behavior.
- Next implementation target: wire real auth and the main Memora query flow.

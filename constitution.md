# Easy Book Constitution

## Project Overview
泳课学员管理系统 — Swimming lesson student management system.

## Tech Stack
- **Backend:** Python 3.12, FastAPI, Motor (MongoDB async driver)
- **Frontend:** Vue 3, Vite, Pinia
- **Database:** MongoDB
- **Port:** Backend runs on 8002, Frontend dev server on 5173

## Architecture
- `backend/api_server/` — FastAPI application
  - `api/` — Route handlers (students, courses, appointments, packages, attendance)
  - `services/` — Business logic layer
  - `models.py` — Pydantic models for validation
  - `mongo_database.py` — MongoDB data access layer
  - `main.py` — Application entry point
- `frontend/src/` — Vue 3 SPA
  - `views/` — Page components
  - `components/` — Reusable UI components
  - `api/` — Backend API client modules
  - `stores/` — Pinia state management

## Conventions
- API responses use Chinese error messages
- Mobile-first design (430px width target)
- MongoDB uses string IDs (not ObjectId)
- All datetime stored as ISO format strings
- Tests use pytest with httpx AsyncClient

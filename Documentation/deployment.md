# Fraud-AI Deployment Guide

This guide documents the correct service deployment order and the correct database alignment for this repository.

## Architecture

- frontend: React + Vite app
- banking_backend: FastAPI service for users, transactions, auth logs
- backend: FastAPI fraud analysis service (rules + ML)
- PostgreSQL: persistent storage
- Redis: runtime support for spike and rate-based logic

## Correct DB Alignment

Use these database names consistently:

- Fraud backend database: fraudai_db
- Banking backend database: hooverbank

Do not mix with banking_db or hooverbank_db unless you intentionally refactor every reference.

### File-to-DB alignment (authoritative)

- backend/.env and backend/.env.example
  - DATABASE_URL should point to fraudai_db
  - DB_NAME should be fraudai_db
- backend/storage/database.py
  - Reads DATABASE_URL from settings, so it follows backend env
- banking_backend/database.py
  - DATABASE_URL should point to hooverbank
- banking_backend/init_db.py
  - DATABASE_URL should point to hooverbank
- banking_backend/init_hooverbank_db.py
  - DATABASE_URL should point to hooverbank

## Required Local Services

- PostgreSQL running and reachable on localhost:5432
- Redis running and reachable on localhost:6379

## One-Time Setup

### 1. Create Python virtual environments and install dependencies

Backend (fraud):

- cd backend
- python -m venv .venv
- .venv\Scripts\activate
- pip install -r requirements.txt

Banking backend:

- cd banking_backend
- python -m venv .venv
- .venv\Scripts\activate
- pip install -r requirements.txt

Frontend:

- cd frontend
- npm install

### 2. Create PostgreSQL databases

Run in psql as a superuser:

- CREATE USER fraudai_user WITH PASSWORD 'password123';
- CREATE DATABASE fraudai_db OWNER fraudai_user;
- CREATE DATABASE hooverbank OWNER fraudai_user;
- GRANT ALL PRIVILEGES ON DATABASE fraudai_db TO fraudai_user;
- GRANT ALL PRIVILEGES ON DATABASE hooverbank TO fraudai_user;

### 3. Configure environment files

Fraud backend env at backend/.env should include:

- DATABASE_URL=postgresql://fraudai_user:password123@localhost:5432/fraudai_db
- DB_HOST=localhost
- DB_PORT=5432
- DB_NAME=fraudai_db
- DB_USER=fraudai_user
- DB_PASSWORD=password123
- REDIS_HOST=localhost
- REDIS_PORT=6379
- REDIS_DB=0
- API_HOST=0.0.0.0
- API_PORT=8000
- SECRET_KEY=<strong-random-secret>

Banking backend currently uses hardcoded DATABASE_URL in code:

- banking_backend/database.py should target
  - postgresql://fraudai_user:password123@localhost:5432/hooverbank

If you later refactor banking backend to env-driven config, keep the same hooverbank target.

### 4. Initialize database tables

Banking tables:

- cd banking_backend
- python init_hooverbank_db.py

Fraud tables:

- cd backend
- python -c "from storage.database import create_tables; create_tables()"

## Start Order

Start services in this order to avoid integration errors:

1. banking_backend on port 8001
2. backend (fraud) on port 8000
3. frontend on port 8080

Commands:

Banking backend:

- cd banking_backend
- uvicorn main:app --host 0.0.0.0 --port 8001 --reload

Fraud backend:

- cd backend
- uvicorn main:app --host 0.0.0.0 --port 8000 --reload

Frontend:

- cd frontend
- npm run dev

## Health Checks

- Banking health: http://localhost:8001/health
- Fraud health: http://localhost:8000/health
- Frontend: http://localhost:8080

## Integration Notes

- Banking backend posts fraud analysis requests to:
  - http://localhost:8000/api/fraud/analyze
- Frontend reads fraud API from VITE_API_URL (default localhost:8000)
- Some frontend calls are hardcoded to localhost:8001 for banking auth/transactions

For production, replace all localhost URLs with environment-based service URLs.

## Common Misalignment Failures

- Error: relation does not exist
  - Cause: tables were created in hooverbank_db but runtime uses hooverbank
  - Fix: recreate tables in hooverbank and keep all banking references on hooverbank

- Error: fraud backend fails on startup with settings validation
  - Cause: missing SECRET_KEY or DB_PASSWORD in backend/.env
  - Fix: add required variables from this guide

- Error: frontend login/transfer fails but page loads
  - Cause: banking backend not running on port 8001
  - Fix: start banking backend first

## Production Checklist

- Move hardcoded URLs to environment variables
- Use non-default strong credentials and secrets
- Restrict CORS to deployed frontend origin
- Run behind HTTPS and reverse proxy
- Add process manager (systemd, supervisord, or containers)
- Add backup policy for both fraudai_db and hooverbank

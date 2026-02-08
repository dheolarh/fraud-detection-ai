# Banking System Backend

Independent banking system for International and Hoover Banks.

## Features
- Location autocomplete with currency detection
- Real-time exchange rate conversion
- Account management and verification
- Inter-bank transfers

## Structure
```
banking_backend/
├── api/              # API routes
├── services/         # Business logic
├── models/           # Data models
└── main.py          # FastAPI app
```

## Running
```bash
cd banking_backend
uvicorn main:app --reload --port 8001
```

Backend runs on http://localhost:8001

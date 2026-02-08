"""
Banking Backend Main Application
Independent FastAPI app for banking services
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router
from api.banking_routes import router as banking_router
from api.auth_routes import router as auth_router

app = FastAPI(
    title="Banking System API",
    description="Independent banking system for International and Hoover Banks",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:8080", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)
app.include_router(banking_router)
app.include_router(auth_router)


@app.get("/")
async def root():
    return {
        "service": "Banking System API",
        "status": "online",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

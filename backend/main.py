"""
FastAPI Main Application
Fraud AI Backend - Real-time fraud detection engine
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from data_retriever.routes import transactions, accounts, fraud, suspicious_logins, cases, analyze
from utils.rate_limiter import rate_limit_middleware
from config.settings import settings

app = FastAPI(
    title="Fraud AI API",
    description="Real-time fraud detection engine for fintech transactions",
    version="1.0.0"
)

logger.info(f"Starting Fraud AI API on {settings.API_HOST}:{settings.API_PORT}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(rate_limit_middleware)

# NOTE: Authentication is handled by Banking Backend (port 8001)
# Fraud backend only handles fraud analysis
app.include_router(transactions.router, prefix="/api/transaction", tags=["Transactions"])
app.include_router(accounts.router, prefix="/api/account", tags=["Accounts"])
app.include_router(fraud.router)
app.include_router(suspicious_logins.router)
app.include_router(cases.router)
app.include_router(analyze.router)


@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "name": "Fraud AI API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "transactions": "/api/transaction",
            "accounts": "/api/account",
            "docs": "/docs"
        },
        "note": "Authentication is handled by Banking Backend (port 8001)"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.on_event("startup")
async def startup_event():
    """
    Application startup event.
    Initializes ML model retraining scheduler.
    """
    logger.info("Starting Fraud AI Backend...")
    
    # Start periodic model retraining (every 30 days)
    try:
        from intelligence.retraining_scheduler import start_retraining_scheduler
        
        # Get retrain interval from settings (default: 30 days)
        retrain_interval = getattr(settings, 'RETRAIN_INTERVAL_DAYS', 30)
        
        start_retraining_scheduler(retrain_interval_days=retrain_interval)
        logger.success(f"✅ Model retraining scheduler started (interval: {retrain_interval} days)")
    except Exception as e:
        logger.error(f"❌ Failed to start model retraining scheduler: {e}")
        logger.warning("⚠️  Continuing without automatic retraining")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Application shutdown event.
    Stops the model retraining scheduler.
    """
    logger.info("Shutting down Fraud AI Backend...")
    
    try:
        from intelligence.retraining_scheduler import stop_retraining_scheduler
        stop_retraining_scheduler()
        logger.info("Model retraining scheduler stopped")
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )

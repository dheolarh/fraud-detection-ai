"""
Periodic Model Retraining Scheduler
Automatically retrains ML models every 30 days using latest data
"""

import schedule
import time
import threading
from datetime import datetime
from loguru import logger
from intelligence.train_models import train_all_models


class ModelRetrainingScheduler:
    """
    Background scheduler for periodic model retraining.
    Runs every 30 days to keep models up-to-date with latest fraud patterns.
    """
    
    def __init__(self, retrain_interval_days: int = 30):
        """
        Initialize the retraining scheduler.
        
        Args:
            retrain_interval_days: Number of days between retraining (default: 30)
        """
        self.retrain_interval_days = retrain_interval_days
        self.is_running = False
        self.thread = None
        
        logger.info(f"Model retraining scheduler initialized (interval: {retrain_interval_days} days)")
    
    def retrain_models(self):
        """
        Execute model retraining.
        Called automatically by the scheduler.
        """
        try:
            logger.info("=" * 80)
            logger.info("STARTING SCHEDULED MODEL RETRAINING")
            logger.info(f"Timestamp: {datetime.now().isoformat()}")
            logger.info("=" * 80)
            
            # Train all models
            success = train_all_models()
            
            if success:
                logger.success("✅ Scheduled model retraining completed successfully")
            else:
                logger.error("❌ Scheduled model retraining failed")
            
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"Error during scheduled model retraining: {e}")
            logger.exception(e)
    
    def _run_scheduler(self):
        """
        Internal method to run the scheduler loop.
        Runs in a separate thread.
        """
        logger.info("Scheduler thread started")
        
        while self.is_running:
            schedule.run_pending()
            time.sleep(3600)  # Check every hour
    
    def start(self):
        """
        Start the periodic retraining scheduler.
        Runs in a background thread.
        """
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        # Schedule the retraining job
        schedule.every(self.retrain_interval_days).days.do(self.retrain_models)
        
        logger.info(f"Scheduled model retraining every {self.retrain_interval_days} days")
        logger.info(f"Next retraining: {schedule.next_run()}")
        
        # Start scheduler in background thread
        self.is_running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        
        logger.success("✅ Model retraining scheduler started successfully")
    
    def stop(self):
        """
        Stop the periodic retraining scheduler.
        """
        if not self.is_running:
            logger.warning("Scheduler is not running")
            return
        
        self.is_running = False
        schedule.clear()
        
        if self.thread:
            self.thread.join(timeout=5)
        
        logger.info("Model retraining scheduler stopped")
    
    def trigger_immediate_retrain(self):
        """
        Trigger an immediate model retraining (manual override).
        Useful for testing or when you want to retrain before the scheduled time.
        """
        logger.info("Manual retraining triggered")
        self.retrain_models()


# Global scheduler instance
_scheduler = None


def get_scheduler(retrain_interval_days: int = 30) -> ModelRetrainingScheduler:
    """
    Get the global scheduler instance (singleton pattern).
    
    Args:
        retrain_interval_days: Number of days between retraining
        
    Returns:
        ModelRetrainingScheduler instance
    """
    global _scheduler
    
    if _scheduler is None:
        _scheduler = ModelRetrainingScheduler(retrain_interval_days)
    
    return _scheduler


def start_retraining_scheduler(retrain_interval_days: int = 30):
    """
    Start the periodic model retraining scheduler.
    Call this when the application starts.
    
    Args:
        retrain_interval_days: Number of days between retraining (default: 30)
    """
    scheduler = get_scheduler(retrain_interval_days)
    scheduler.start()


def stop_retraining_scheduler():
    """
    Stop the periodic model retraining scheduler.
    Call this when the application shuts down.
    """
    global _scheduler
    
    if _scheduler:
        _scheduler.stop()


def trigger_manual_retrain():
    """
    Trigger an immediate model retraining.
    Useful for manual updates or testing.
    """
    scheduler = get_scheduler()
    scheduler.trigger_immediate_retrain()


if __name__ == "__main__":
    # Test the scheduler
    logger.info("Testing model retraining scheduler...")
    
    # Create scheduler with 1-minute interval for testing
    test_scheduler = ModelRetrainingScheduler(retrain_interval_days=1/1440)  # 1 minute
    test_scheduler.start()
    
    # Keep running for 5 minutes
    logger.info("Scheduler will run for 5 minutes (for testing)")
    time.sleep(300)
    
    test_scheduler.stop()
    logger.info("Test complete")

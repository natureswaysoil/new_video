#!/usr/bin/env python3
"""
Scheduler for Video Automation
Runs the automation at specified intervals
"""

import schedule
import time
import logging
import sys
from datetime import datetime
from video_automation import VideoAutomation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AutomationScheduler:
    """Schedules and runs video automation"""
    
    def __init__(self, config: dict):
        self.config = config
        self.automation = None
    
    def run_automation(self):
        """Run the automation"""
        try:
            logger.info(f"\n{'='*60}")
            logger.info(f"Starting scheduled automation run at {datetime.now()}")
            logger.info(f"{'='*60}\n")
            
            # Create new automation instance
            self.automation = VideoAutomation(self.config)
            
            # Process configured number of products
            process_count = self.config.get('products_per_run', 1)
            self.automation.run(process_count=process_count)
            
            logger.info(f"\n{'='*60}")
            logger.info(f"Scheduled run completed at {datetime.now()}")
            logger.info(f"{'='*60}\n")
            
        except Exception as e:
            logger.error(f"Scheduled run failed: {e}", exc_info=True)
    
    def start(self):
        """Start the scheduler"""
        schedule_type = self.config.get('schedule_type', 'daily')
        schedule_time = self.config.get('schedule_time', '09:00')
        
        if schedule_type == 'daily':
            schedule.every().day.at(schedule_time).do(self.run_automation)
            logger.info(f"Scheduler: Will run daily at {schedule_time}")
            
        elif schedule_type == 'hourly':
            schedule.every().hour.do(self.run_automation)
            logger.info("Scheduler: Will run every hour")
            
        elif schedule_type == 'every_n_hours':
            hours = self.config.get('schedule_interval_hours', 4)
            schedule.every(hours).hours.do(self.run_automation)
            logger.info(f"Scheduler: Will run every {hours} hours")
            
        elif schedule_type == 'custom':
            # Custom schedule - run multiple times per day
            times = self.config.get('schedule_times', ['09:00', '15:00', '21:00'])
            for time_str in times:
                schedule.every().day.at(time_str).do(self.run_automation)
            logger.info(f"Scheduler: Will run daily at {', '.join(times)}")
        
        # Run immediately on start if configured
        if self.config.get('run_on_start', False):
            logger.info("Running automation immediately on startup")
            self.run_automation()
        
        # Keep running
        logger.info("Scheduler started. Press Ctrl+C to stop.")
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("\nScheduler stopped by user")
            sys.exit(0)


def main():
    """Main entry point"""
    import os
    
    # Configuration
    config = {
        'gcp_project_id': os.getenv('GCP_PROJECT_ID', 'your-project-id'),
        'spreadsheet_id': '1LU2ahpzMqLB5FLYqiyDbXOfjTxbdp8U8',
        
        # Scheduling options
        'schedule_type': os.getenv('SCHEDULE_TYPE', 'daily'),  # daily, hourly, every_n_hours, custom
        'schedule_time': os.getenv('SCHEDULE_TIME', '09:00'),  # For daily schedule
        'schedule_interval_hours': int(os.getenv('SCHEDULE_INTERVAL_HOURS', '4')),  # For every_n_hours
        'schedule_times': ['09:00', '15:00', '21:00'],  # For custom schedule
        
        # Processing options
        'products_per_run': int(os.getenv('PRODUCTS_PER_RUN', '1')),
        'run_on_start': os.getenv('RUN_ON_START', 'false').lower() == 'true'
    }
    
    # Start scheduler
    scheduler = AutomationScheduler(config)
    scheduler.start()


if __name__ == "__main__":
    main()

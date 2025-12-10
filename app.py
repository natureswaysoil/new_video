#!/usr/bin/env python3
"""
Flask HTTP wrapper for Video Automation CLI
Exposes the video automation as an HTTP service for Cloud Run
"""

import os
import json
import uuid
import logging
import threading
import yaml
from datetime import datetime
from typing import Dict, Optional
from flask import Flask, request, jsonify
from video_automation import VideoAutomation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# In-memory job storage (for production, use Redis or database)
jobs = {}
jobs_lock = threading.Lock()


class JobStatus:
    """Job status constants"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


def create_job(profile_id: str, config: Optional[Dict] = None) -> str:
    """Create a new job and return job_id"""
    job_id = str(uuid.uuid4())
    
    with jobs_lock:
        jobs[job_id] = {
            'job_id': job_id,
            'profile_id': profile_id,
            'config': config,
            'status': JobStatus.PENDING,
            'created_at': datetime.now().isoformat(),
            'started_at': None,
            'completed_at': None,
            'error': None,
            'result': None
        }
    
    logger.info(f"Created job {job_id} for profile {profile_id}")
    return job_id


def update_job_status(job_id: str, status: str, **kwargs):
    """Update job status and additional fields"""
    with jobs_lock:
        if job_id in jobs:
            jobs[job_id]['status'] = status
            jobs[job_id].update(kwargs)
            logger.info(f"Job {job_id} status updated to {status}")


def get_job_status(job_id: str) -> Optional[Dict]:
    """Get job status"""
    with jobs_lock:
        return jobs.get(job_id)


def run_automation_job(job_id: str, profile_id: str, config: Dict):
    """Run the automation in a background thread"""
    try:
        update_job_status(
            job_id, 
            JobStatus.RUNNING,
            started_at=datetime.now().isoformat()
        )
        
        logger.info(f"Starting automation job {job_id}")
        
        # Create automation instance
        automation = VideoAutomation(config)
        
        # Process configured number of products (default to 1)
        process_count = config.get('products_per_run', 1)
        automation.run(process_count=process_count)
        
        # Update job status
        update_job_status(
            job_id,
            JobStatus.COMPLETED,
            completed_at=datetime.now().isoformat(),
            result={'message': 'Automation completed successfully', 'products_processed': process_count}
        )
        
        logger.info(f"Job {job_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}", exc_info=True)
        update_job_status(
            job_id,
            JobStatus.FAILED,
            completed_at=datetime.now().isoformat(),
            error=str(e)
        )


@app.route('/', methods=['GET'])
def service_info():
    """Service information endpoint"""
    return jsonify({
        'service': 'Video Automation HTTP Service',
        'version': '1.0.0',
        'description': 'HTTP wrapper for video automation CLI',
        'endpoints': {
            '/': 'Service information',
            '/health': 'Health check',
            '/run': 'Start automation job (POST)',
            '/status/<job_id>': 'Get job status'
        }
    })


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Cloud Run"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    }), 200


@app.route('/run', methods=['POST'])
def run_automation():
    """
    Start a new automation job
    
    Request body (JSON):
    {
        "profile_id": "profile123",
        "config": "yaml config text" (optional),
        "config_path": "/path/to/config.yaml" (optional)
    }
    
    Returns:
    {
        "job_id": "uuid",
        "status": "pending",
        "status_url": "/status/<job_id>"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body must be JSON'}), 400
        
        profile_id = data.get('profile_id')
        if not profile_id:
            return jsonify({'error': 'profile_id is required'}), 400
        
        # Get configuration from either config text or config_path
        config = None
        
        if 'config' in data:
            # Parse YAML config text
            try:
                config = yaml.safe_load(data['config'])
            except yaml.YAMLError as e:
                return jsonify({'error': f'Invalid YAML config: {str(e)}'}), 400
        
        elif 'config_path' in data:
            # Load config from file path
            config_path = data['config_path']
            try:
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
            except FileNotFoundError:
                return jsonify({'error': f'Config file not found: {config_path}'}), 404
            except yaml.YAMLError as e:
                return jsonify({'error': f'Invalid YAML in config file: {str(e)}'}), 400
            except Exception as e:
                return jsonify({'error': f'Error reading config file: {str(e)}'}), 500
        
        else:
            # Use default configuration
            config = {
                'gcp_project_id': os.getenv('GCP_PROJECT_ID', 'your-project-id'),
                'spreadsheet_id': os.getenv('SPREADSHEET_ID', '1LU2ahpzMqLB5FLYqiyDbXOfjTxbdp8U8'),
                'products_per_run': int(os.getenv('PRODUCTS_PER_RUN', '1'))
            }
        
        # Ensure required config fields
        if 'gcp_project_id' not in config:
            config['gcp_project_id'] = os.getenv('GCP_PROJECT_ID', 'your-project-id')
        
        if 'spreadsheet_id' not in config:
            config['spreadsheet_id'] = os.getenv('SPREADSHEET_ID', '1LU2ahpzMqLB5FLYqiyDbXOfjTxbdp8U8')
        
        # Create job
        job_id = create_job(profile_id, config)
        
        # Start background thread
        thread = threading.Thread(
            target=run_automation_job,
            args=(job_id, profile_id, config),
            daemon=True
        )
        thread.start()
        
        # Return job information
        return jsonify({
            'job_id': job_id,
            'status': JobStatus.PENDING,
            'status_url': f'/status/{job_id}'
        }), 202
        
    except Exception as e:
        logger.error(f"Error starting job: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/status/<job_id>', methods=['GET'])
def job_status(job_id: str):
    """
    Get status of a job
    
    Returns:
    {
        "job_id": "uuid",
        "profile_id": "profile123",
        "status": "pending|running|completed|failed",
        "created_at": "timestamp",
        "started_at": "timestamp",
        "completed_at": "timestamp",
        "error": "error message if failed",
        "result": "result data if completed"
    }
    """
    job = get_job_status(job_id)
    
    if not job:
        return jsonify({'error': f'Job {job_id} not found'}), 404
    
    return jsonify(job), 200


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal error: {error}", exc_info=True)
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    # For local development
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)

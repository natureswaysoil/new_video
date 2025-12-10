# Flask HTTP API Documentation

This document describes the HTTP API endpoints for the Video Automation service.

## Base URL

When deployed to Cloud Run:
```
https://video-automation-<hash>.<region>.run.app
```

For local development:
```
http://localhost:8080
```

## Endpoints

### GET /

Returns service information.

**Response:**
```json
{
  "service": "Video Automation HTTP Service",
  "version": "1.0.0",
  "description": "HTTP wrapper for video automation CLI",
  "endpoints": {
    "/": "Service information",
    "/health": "Health check",
    "/run": "Start automation job (POST)",
    "/status/<job_id>": "Get job status"
  }
}
```

### GET /health

Health check endpoint used by Cloud Run for liveness probes.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-12-10T22:33:00.000000"
}
```

**Status Code:** `200 OK`

### POST /run

Start a new video automation job in the background.

**Request Headers:**
- `Content-Type: application/json`

**Request Body:**
```json
{
  "profile_id": "profile123",
  "config": "optional YAML config text",
  "config_path": "optional path to config file"
}
```

**Parameters:**
- `profile_id` (required): Identifier for the profile/job
- `config` (optional): YAML configuration as text string
- `config_path` (optional): Path to YAML configuration file

If neither `config` nor `config_path` is provided, the service uses environment variables:
- `GCP_PROJECT_ID` (required)
- `SPREADSHEET_ID` (required)
- `PRODUCTS_PER_RUN` (optional, default: 1, max: 10)

**Configuration Format (YAML):**
```yaml
gcp_project_id: your-project-id
spreadsheet_id: your-spreadsheet-id
products_per_run: 1  # Max 10
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "status_url": "/status/550e8400-e29b-41d4-a716-446655440000"
}
```

**Status Code:** `202 Accepted`

**Error Responses:**

400 Bad Request:
```json
{
  "error": "profile_id is required"
}
```

```json
{
  "error": "Invalid YAML config: <error details>"
}
```

```json
{
  "error": "products_per_run cannot exceed 10"
}
```

500 Internal Server Error:
```json
{
  "error": "GCP_PROJECT_ID environment variable is required"
}
```

### GET /status/<job_id>

Get the status of a job.

**Path Parameters:**
- `job_id`: The UUID of the job returned by POST /run

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "profile_id": "profile123",
  "status": "running",
  "config": {
    "gcp_project_id": "project-id",
    "spreadsheet_id": "sheet-id",
    "products_per_run": 1
  },
  "created_at": "2025-12-10T22:33:00.000000",
  "started_at": "2025-12-10T22:33:01.000000",
  "completed_at": null,
  "error": null,
  "result": null
}
```

**Status Values:**
- `pending`: Job created but not yet started
- `running`: Job is currently processing
- `completed`: Job finished successfully
- `failed`: Job encountered an error

**Completed Job Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "profile_id": "profile123",
  "status": "completed",
  "config": {...},
  "created_at": "2025-12-10T22:33:00.000000",
  "started_at": "2025-12-10T22:33:01.000000",
  "completed_at": "2025-12-10T22:35:00.000000",
  "error": null,
  "result": {
    "message": "Automation completed successfully",
    "products_processed": 1
  }
}
```

**Failed Job Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "profile_id": "profile123",
  "status": "failed",
  "config": {...},
  "created_at": "2025-12-10T22:33:00.000000",
  "started_at": "2025-12-10T22:33:01.000000",
  "completed_at": "2025-12-10T22:34:00.000000",
  "error": "Authentication failed: Invalid credentials",
  "result": null
}
```

**Status Code:** `200 OK`

**Error Response:**
```json
{
  "error": "Job 550e8400-e29b-41d4-a716-446655440000 not found"
}
```

**Status Code:** `404 Not Found`

## Example Usage

### Using curl

Start a job with default configuration:
```bash
curl -X POST https://your-service.run.app/run \
  -H "Content-Type: application/json" \
  -d '{"profile_id": "my-profile"}'
```

Start a job with custom YAML config:
```bash
curl -X POST https://your-service.run.app/run \
  -H "Content-Type: application/json" \
  -d '{
    "profile_id": "my-profile",
    "config": "gcp_project_id: my-project\nspreadsheet_id: my-sheet\nproducts_per_run: 2"
  }'
```

Check job status:
```bash
curl https://your-service.run.app/status/550e8400-e29b-41d4-a716-446655440000
```

### Using Python

```python
import requests
import time

# Start a job
response = requests.post(
    'https://your-service.run.app/run',
    json={'profile_id': 'my-profile'}
)
job = response.json()
job_id = job['job_id']
print(f"Started job: {job_id}")

# Poll for completion
while True:
    response = requests.get(f'https://your-service.run.app/status/{job_id}')
    status = response.json()
    
    if status['status'] in ['completed', 'failed']:
        print(f"Job {status['status']}")
        if status['status'] == 'completed':
            print(f"Result: {status['result']}")
        else:
            print(f"Error: {status['error']}")
        break
    
    print(f"Job status: {status['status']}")
    time.sleep(10)
```

## Important Notes

### Job State Persistence

**⚠️ WARNING:** Job state is stored in-memory and will be lost when the container restarts. This means:

- Jobs in progress will be terminated if the container stops
- Job history will be lost on deployment updates
- For production use, consider implementing persistent storage (Redis, Cloud Firestore, etc.)

### Resource Limits

- Maximum products per run: 10
- Request timeout: 30 minutes (1800 seconds)
- Background jobs use daemon threads and may be terminated during container shutdown

### Authentication

The API itself does not require authentication, but the video automation service requires:
- GCP credentials (via Application Default Credentials)
- Access to Google Secret Manager for API keys

Ensure proper authentication is configured when deploying to Cloud Run.

## Environment Variables

Required environment variables for the service:

- `GCP_PROJECT_ID`: Google Cloud Project ID
- `SPREADSHEET_ID`: Google Sheets spreadsheet ID
- `PORT` (optional): HTTP port (default: 8080)
- `PRODUCTS_PER_RUN` (optional): Default number of products to process (default: 1, max: 10)

## Deployment

See the main README.md for deployment instructions to Google Cloud Run.

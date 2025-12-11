# Amazon PPC Optimizer

This module provides functionality to fetch and analyze Amazon Advertising API campaign reports with proper configuration.

## Overview

The Amazon PPC Optimizer correctly implements the Amazon Advertising API reporting endpoint with all required fields, specifically including the `adProduct` field that was previously missing.

## Key Features

- ✅ Properly configured API payload with dynamic `adProduct` field
- ✅ Support for Sponsored Products, Sponsored Brands, and Sponsored Display campaigns
- ✅ Flexible date range generation
- ✅ Report creation and status tracking
- ✅ Report download functionality
- ✅ Comprehensive logging and error handling

## Corrected Payload Structure

The key fix in this implementation is the inclusion of the `adProduct` field in the configuration, which is now dynamically determined based on the `report_type`:

```python
# ✅ CORRECTED - Dynamic adProduct based on report_type
payload = {
    "startDate": "2025-12-01",
    "endDate": "2025-12-09",
    "configuration": {
        "adProduct": "SPONSORED_PRODUCTS",  # Dynamically set based on report_type
        "columns": ["campaignName", "impressions", "clicks", "cost"],
        "reportTypeId": "spCampaigns",
        "timeUnit": "DAILY",
        "format": "GZIP_JSON"
    }
}
```

### Report Type to adProduct Mapping

The optimizer automatically maps report types to the correct adProduct value:

- **Sponsored Products**: `spCampaigns`, `spAdGroups`, `spKeywords`, `spTargets` → `SPONSORED_PRODUCTS`
- **Sponsored Brands**: `sbCampaigns`, `sbAdGroups`, `sbKeywords` → `SPONSORED_BRANDS`
- **Sponsored Display**: `sdCampaigns`, `sdAdGroups`, `sdTargets` → `SPONSORED_DISPLAY`

### Previous Issue

The original code was missing the `adProduct` field:

```python
# ❌ INCORRECT (Missing adProduct)
payload = {
    "startDate": "2025-12-01",
    "endDate": "2025-12-09",
    "configuration": {
        "columns": ["campaignName", "impressions", "clicks", "cost"],
        "reportTypeId": "spCampaigns",
        "timeUnit": "DAILY",
        "format": "GZIP_JSON"
    }
}
```

## Environment Variables

Set the following environment variables before running:

- `AMAZON_API_ENDPOINT`: Amazon Advertising API endpoint (default: https://advertising-api.amazon.com)
  - **Note**: Amazon Advertising API uses region-specific endpoints:
    - North America: `https://advertising-api.amazon.com`
    - Europe: `https://advertising-api-eu.amazon.com`
    - Far East: `https://advertising-api-fe.amazon.com`
  - Choose the endpoint that matches your marketplace region
- `AMAZON_ACCESS_TOKEN`: Your Amazon Advertising API access token (required)
- `AMAZON_CLIENT_ID`: Your Amazon Advertising API client ID (required)

## Usage

### Basic Usage

```python
from amazon_ppc_optimizer import AmazonPPCOptimizer

# Initialize the optimizer
optimizer = AmazonPPCOptimizer(
    api_endpoint="https://advertising-api.amazon.com",
    access_token="your-access-token",
    client_id="your-client-id"  # Required
)

# Create a campaign report
report = optimizer.create_campaign_report(
    start_date="2025-12-01",
    end_date="2025-12-09",
    columns=["campaignName", "impressions", "clicks", "cost"],
    report_type="spCampaigns"
)

print(f"Report ID: {report['reportId']}")
```

### Running as a Standalone Script

```bash
export AMAZON_ACCESS_TOKEN="your-access-token"
export AMAZON_CLIENT_ID="your-client-id"
python amazon_ppc_optimizer.py
```

## Deployment

### Deploy to Google Cloud

#### Option 1: Using the Deployment Script

```bash
export GCP_PROJECT_ID=your-project-id

# Interactive mode (will prompt for Cloud Run deployment)
./deploy-amazon-ppc.sh

# Non-interactive mode (skip Cloud Run deployment)
export DEPLOY_TO_CLOUD_RUN=no
./deploy-amazon-ppc.sh

# Non-interactive mode (auto-deploy to Cloud Run)
export DEPLOY_TO_CLOUD_RUN=yes
./deploy-amazon-ppc.sh
```

#### Option 2: Using Cloud Build

```bash
gcloud builds submit --config=cloudbuild-amazon-ppc.yaml
```

This will build and push the Docker image to:
```
us-central1-docker.pkg.dev/PROJECT_ID/amazon-ppc-repo/amazon-ppc-optimizer:latest
```

### Docker Deployment

Build the Docker image:

```bash
docker build -f Dockerfile.amazon-ppc -t amazon-ppc-optimizer .
```

Run the container:

```bash
docker run -e AMAZON_ACCESS_TOKEN="your-token" \
           -e AMAZON_CLIENT_ID="your-client-id" \
           amazon-ppc-optimizer
```

## API Reference

### AmazonPPCOptimizer Class

#### `create_campaign_report(start_date, end_date, columns=None, report_type="spCampaigns")`

Creates a campaign report request with proper configuration including the required `adProduct` field.

**Parameters:**
- `start_date` (str): Report start date in YYYY-MM-DD format
- `end_date` (str): Report end date in YYYY-MM-DD format
- `columns` (list, optional): List of columns to include. Default: ["campaignName", "impressions", "clicks", "cost"]
- `report_type` (str, optional): Type of report. Default: "spCampaigns"

**Returns:**
- Dict containing the report request response with reportId

#### `get_report_status(report_id)`

Checks the status of a report.

**Parameters:**
- `report_id` (str): The ID of the report to check

**Returns:**
- Dict containing the report status

#### `download_report(download_url)`

Downloads the completed report.

**Parameters:**
- `download_url` (str): The URL to download the report from

**Returns:**
- bytes: The report data

#### `generate_date_range(days_back=7)`

Generates a date range for reporting.

**Parameters:**
- `days_back` (int, optional): Number of days to look back from today. Default: 7

**Returns:**
- tuple: (start_date, end_date) as strings in YYYY-MM-DD format

## Supported Report Types

The optimizer supports all major Amazon Advertising report types:

### Sponsored Products
- `spCampaigns` - Sponsored Products Campaigns
- `spAdGroups` - Sponsored Products Ad Groups
- `spKeywords` - Sponsored Products Keywords
- `spTargets` - Sponsored Products Targets

### Sponsored Brands
- `sbCampaigns` - Sponsored Brands Campaigns
- `sbAdGroups` - Sponsored Brands Ad Groups
- `sbKeywords` - Sponsored Brands Keywords

### Sponsored Display
- `sdCampaigns` - Sponsored Display Campaigns
- `sdAdGroups` - Sponsored Display Ad Groups
- `sdTargets` - Sponsored Display Targets

The `adProduct` field is automatically set based on the `report_type` prefix (sp, sb, or sd).

## Supported Columns

Common columns include:
- `campaignName`
- `impressions`
- `clicks`
- `cost`
- `conversions`
- `sales`
- `acos` (Advertising Cost of Sales)
- `roas` (Return on Ad Spend)

Refer to the [Amazon Advertising API documentation](https://advertising.amazon.com/API/docs/en-us/reporting/v3/overview) for the complete list of available columns.

## Logging

The optimizer uses console-only logging optimized for cloud deployments:
- Console output with timestamps (stdout/stderr)
- Suitable for Cloud Run and other containerized environments
- Debug-level logging for payloads (when enabled)
- All logs are automatically collected by cloud logging services

## Error Handling

All API requests include proper error handling with detailed error messages and response logging.

## License

This module is part of the Video Automation System project.

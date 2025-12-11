#!/usr/bin/env python3
"""
Amazon PPC Optimizer
Fetches Amazon Advertising API campaign reports with proper configuration
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
import requests

# Configure logging
# Use console-only logging for cloud deployments (Cloud Run, etc.)
# In containerized environments, logs should go to stdout/stderr for proper log collection
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AmazonPPCOptimizer:
    """Handles Amazon PPC campaign reporting and optimization"""
    
    def __init__(self, api_endpoint: str, access_token: str, client_id: Optional[str] = None):
        """
        Initialize the Amazon PPC Optimizer
        
        Args:
            api_endpoint: The Amazon Advertising API endpoint
            access_token: API access token for authentication
            client_id: Amazon Advertising API client ID (optional, defaults to env var)
        """
        self.api_endpoint = api_endpoint
        
        # Get client ID from parameter or environment variable
        client_id = client_id or os.getenv("AMAZON_CLIENT_ID")
        if not client_id:
            raise ValueError("AMAZON_CLIENT_ID is required. Provide it as a parameter or set the environment variable.")
        
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Amazon-Advertising-API-ClientId": client_id,
        }
    
    def create_campaign_report(
        self, 
        start_date: str, 
        end_date: str,
        columns: list = None,
        report_type: str = "spCampaigns"
    ) -> Dict:
        """
        Create a campaign report request with proper configuration
        
        Args:
            start_date: Report start date in YYYY-MM-DD format
            end_date: Report end date in YYYY-MM-DD format
            columns: List of columns to include in the report
            report_type: Type of report (default: spCampaigns)
            
        Returns:
            Dict containing the report request response
        """
        try:
            if columns is None:
                columns = ["campaignName", "impressions", "clicks", "cost"]
            
            # Map report_type to adProduct
            report_type_to_ad_product = {
                "spCampaigns": "SPONSORED_PRODUCTS",
                "spAdGroups": "SPONSORED_PRODUCTS",
                "spKeywords": "SPONSORED_PRODUCTS",
                "spTargets": "SPONSORED_PRODUCTS",
                "sbCampaigns": "SPONSORED_BRANDS",
                "sbAdGroups": "SPONSORED_BRANDS",
                "sbKeywords": "SPONSORED_BRANDS",
                "sdCampaigns": "SPONSORED_DISPLAY",
                "sdAdGroups": "SPONSORED_DISPLAY",
                "sdTargets": "SPONSORED_DISPLAY"
            }
            ad_product = report_type_to_ad_product.get(report_type)
            if not ad_product:
                raise ValueError(f"Unsupported report_type '{report_type}'. Supported types: {list(report_type_to_ad_product.keys())}")
            
            # ✅ CORRECTED payload with dynamic adProduct field
            payload = {
                "startDate": start_date,
                "endDate": end_date,
                "configuration": {
                    "adProduct": ad_product,
                    "columns": columns,
                    "reportTypeId": report_type,
                    "timeUnit": "DAILY",
                    "format": "GZIP_JSON"
                }
            }
            
            logger.info(f"Creating campaign report from {start_date} to {end_date}")
            logger.debug(f"Payload: {json.dumps(payload, indent=2)}")
            
            url = f"{self.api_endpoint}/reporting/reports"
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Report created successfully: {result}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating campaign report: {e}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                logger.error(f"Response: {e.response.text}")
            raise
    
    def get_report_status(self, report_id: str) -> Dict:
        """
        Check the status of a report
        
        Args:
            report_id: The ID of the report to check
            
        Returns:
            Dict containing the report status
        """
        try:
            url = f"{self.api_endpoint}/reporting/reports/{report_id}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Report status: {result.get('status', 'Unknown')}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error checking report status: {e}")
            raise
    
    def download_report(self, download_url: str) -> bytes:
        """
        Download the completed report
        
        Args:
            download_url: The URL to download the report from
            
        Returns:
            bytes: The report data
        """
        try:
            response = requests.get(download_url, headers=self.headers)
            response.raise_for_status()
            
            logger.info("Report downloaded successfully")
            return response.content
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error downloading report: {e}")
            raise
    
    def generate_date_range(self, days_back: int = 7) -> tuple:
        """
        Generate a date range for reporting
        
        Args:
            days_back: Number of days to look back from today
            
        Returns:
            tuple: (start_date, end_date) as strings in YYYY-MM-DD format
        """
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days_back)
        
        return str(start_date), str(end_date)


def main():
    """Main function for testing the Amazon PPC Optimizer"""
    # Example usage
    api_endpoint = os.getenv("AMAZON_API_ENDPOINT", "https://advertising-api.amazon.com")
    access_token = os.getenv("AMAZON_ACCESS_TOKEN", "")
    client_id = os.getenv("AMAZON_CLIENT_ID", "")
    
    if not access_token:
        raise ValueError(
            "AMAZON_ACCESS_TOKEN environment variable is required. "
            "Please set it using 'export AMAZON_ACCESS_TOKEN=your_token' in your shell or environment."
        )
    
    if not client_id:
        raise ValueError(
            "AMAZON_CLIENT_ID environment variable is required. "
            "Please set it using 'export AMAZON_CLIENT_ID=your_client_id' in your shell or environment."
        )
    
    optimizer = AmazonPPCOptimizer(api_endpoint, access_token, client_id)
    
    # Generate date range (last 7 days)
    start_date, end_date = optimizer.generate_date_range(days_back=7)
    
    # Create campaign report with corrected payload
    try:
        report = optimizer.create_campaign_report(
            start_date=start_date,
            end_date=end_date,
            columns=["campaignName", "impressions", "clicks", "cost"],
            report_type="spCampaigns"
        )
        logger.info(f"Report created with ID: {report.get('reportId', 'Unknown')}")
    except Exception as e:
        logger.error(f"Failed to create report: {e}")


if __name__ == "__main__":
    main()

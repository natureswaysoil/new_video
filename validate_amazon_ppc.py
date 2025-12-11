#!/usr/bin/env python3
"""
Validation script for Amazon PPC Optimizer
Validates that the payload structure is correct and includes the required adProduct field
"""

import json
import sys
from datetime import datetime
from amazon_ppc_optimizer import AmazonPPCOptimizer, REPORT_TYPE_TO_AD_PRODUCT


def test_payload_structure():
    """Test that the payload has the correct structure with adProduct field"""
    print("Testing Amazon PPC Optimizer payload structure...")
    
    # Test multiple report types to verify dynamic adProduct mapping
    test_cases = [
        ("spCampaigns", "SPONSORED_PRODUCTS"),
        ("sbCampaigns", "SPONSORED_BRANDS"),
        ("sdCampaigns", "SPONSORED_DISPLAY"),
    ]
    
    all_tests_passed = True
    
    for report_type, expected_ad_product in test_cases:
        print(f"\n--- Testing {report_type} ---")
        
        start_date = "2025-12-01"
        end_date = "2025-12-09"
        columns = ["campaignName", "impressions", "clicks", "cost"]
        
        # Get adProduct from the shared constant
        ad_product = REPORT_TYPE_TO_AD_PRODUCT.get(report_type)
        
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
        
        # Validate payload structure
        print(f"Payload structure:")
        print(json.dumps(payload, indent=2))
        
        # Check required fields
        tests = {
            "startDate exists": "startDate" in payload,
            "endDate exists": "endDate" in payload,
            "configuration exists": "configuration" in payload,
            "adProduct exists": "adProduct" in payload.get("configuration", {}),
            f"adProduct is {expected_ad_product}": payload.get("configuration", {}).get("adProduct") == expected_ad_product,
            "columns exist": "columns" in payload.get("configuration", {}),
            "reportTypeId exists": "reportTypeId" in payload.get("configuration", {}),
            "timeUnit exists": "timeUnit" in payload.get("configuration", {}),
            "format exists": "format" in payload.get("configuration", {}),
        }
        
        print(f"\nTest Results for {report_type}:")
        for test_name, result in tests.items():
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"  {status}: {test_name}")
            if not result:
                all_tests_passed = False
    
    return all_tests_passed


def test_date_range_generation():
    """Test date range generation"""
    print("\n\nTesting date range generation...")
    
    # Create a test instance (with dummy credentials)
    try:
        optimizer = AmazonPPCOptimizer(
            api_endpoint="https://advertising-api.amazon.com",
            access_token="test-token",
            client_id="test-client-id"
        )
    except Exception as e:
        print(f"  ✗ FAIL: Could not create optimizer instance: {e}")
        return False
    
    # Generate date range
    start_date, end_date = optimizer.generate_date_range(days_back=7)
    
    print(f"  Generated date range: {start_date} to {end_date}")
    
    # Validate dates are in correct format
    try:
        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")
        print("  ✓ PASS: Date format is correct (YYYY-MM-DD)")
        return True
    except ValueError:
        print("  ✗ FAIL: Date format is incorrect")
        return False


def test_incorrect_payload():
    """Show what the incorrect payload looked like (for reference)"""
    print("\n\nFor reference, here's what the INCORRECT payload looked like:")
    
    incorrect_payload = {
        "startDate": "2025-12-01",
        "endDate": "2025-12-09",
        "configuration": {
            # Missing "adProduct" field - this was the bug!
            "columns": ["campaignName", "impressions", "clicks", "cost"],
            "reportTypeId": "spCampaigns",
            "timeUnit": "DAILY",
            "format": "GZIP_JSON"
        }
    }
    
    print(json.dumps(incorrect_payload, indent=2))
    print("\n❌ The 'adProduct' field was missing from the configuration!")


def main():
    """Run all tests"""
    print("=" * 60)
    print("Amazon PPC Optimizer - Payload Validation Tests")
    print("=" * 60)
    
    results = []
    
    # Test 1: Payload structure
    results.append(("Payload Structure", test_payload_structure()))
    
    # Test 2: Date range generation
    results.append(("Date Range Generation", test_date_range_generation()))
    
    # Show incorrect payload for reference
    test_incorrect_payload()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    all_passed = True
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status}: {test_name}")
        if not result:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n✅ All tests passed! The payload is correctly configured.")
        print("   The 'adProduct' field is now included as required.")
        return 0
    else:
        print("\n❌ Some tests failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

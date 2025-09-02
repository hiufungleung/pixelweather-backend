#!/usr/bin/env python3
"""
Docker health check script
Works internally without exposing ports
"""

import os
import sys
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def health_check():
    """Perform health check"""
    try:
        port = os.getenv('PORT', '5001')
        url = f'http://localhost:{port}/health'
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        # Create session with retry
        session = requests.Session()
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        
        # Make request with timeout
        response = session.get(url, timeout=10)
        response.raise_for_status()
        
        # Check response content
        health_data = response.json()
        if health_data.get('status') == 'healthy':
            print(f"✅ Health check passed: {health_data.get('message', 'OK')}")
            return 0
        else:
            print(f"❌ Health check failed: {health_data}")
            return 1
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check failed: {e}")
        return 1
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(health_check())
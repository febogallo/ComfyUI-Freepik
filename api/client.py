"""
Freepik API Client
Handles all HTTP communication with Freepik API
"""

import requests
import time
import json
from typing import Dict, Any, Optional, List
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class FreepikAPIClient:
    """Base client for Freepik API communication"""
    
    BASE_URL = "https://api.freepik.com"
    API_VERSION = "v1"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.session = self._create_session()
        
    def _create_session(self) -> requests.Session:
        """Create requests session with retry logic"""
        session = requests.Session()
        
        # Retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def set_api_key(self, api_key: str):
        """Set or update API key"""
        self.api_key = api_key
        
    def _get_headers(self) -> Dict[str, str]:
        """Generate request headers with API key"""
        if not self.api_key:
            raise ValueError("API key not set. Use set_api_key() method.")
        
        return {
            "x-freepik-api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def _build_url(self, endpoint: str) -> str:
        """Build full API URL from endpoint"""
        # Remove leading slash if present
        endpoint = endpoint.lstrip('/')
        return f"{self.BASE_URL}/{endpoint}"
    
    def post(self, endpoint: str, data: Dict[str, Any], 
             files: Optional[Dict] = None) -> Dict[str, Any]:
        """
        POST request to Freepik API
        
        Args:
            endpoint: API endpoint (e.g., '/v1/ai/mystic')
            data: Request payload
            files: Optional files for multipart upload
            
        Returns:
            Response JSON as dict
        """
        url = self._build_url(endpoint)
        headers = self._get_headers()
        
        try:
            if files:
                # For file uploads, remove Content-Type header (requests will set it)
                headers.pop('Content-Type', None)
                response = self.session.post(
                    url,
                    data=data,
                    files=files,
                    headers=headers,
                    timeout=30
                )
            else:
                response = self.session.post(
                    url,
                    json=data,
                    headers=headers,
                    timeout=30
                )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP Error {e.response.status_code}"
            try:
                error_detail = e.response.json()
                error_msg += f": {error_detail}"
            except:
                error_msg += f": {e.response.text}"
            raise Exception(error_msg)
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {str(e)}")
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        GET request to Freepik API
        
        Args:
            endpoint: API endpoint
            params: Optional query parameters
            
        Returns:
            Response JSON as dict
        """
        url = self._build_url(endpoint)
        headers = self._get_headers()
        
        try:
            response = self.session.get(
                url,
                params=params,
                headers=headers,
                timeout=30
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP Error {e.response.status_code}"
            try:
                error_detail = e.response.json()
                error_msg += f": {error_detail}"
            except:
                error_msg += f": {e.response.text}"
            raise Exception(error_msg)
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {str(e)}")
    
    def create_task(self, endpoint: str, params: Dict[str, Any], 
                   files: Optional[Dict] = None) -> str:
        """
        Create an async task and return task_id
        
        Args:
            endpoint: API endpoint
            params: Task parameters
            files: Optional files for upload
            
        Returns:
            task_id string
        """
        response = self.post(endpoint, params, files)
        print(f"🔍 DEBUG - Create task full response: {response}")
        
        # Handle different response formats
        if 'data' in response:
            if 'task_id' in response['data']:
                return response['data']['task_id']
            elif 'id' in response['data']:
                return response['data']['id']
        elif 'task_id' in response:
            return response['task_id']
        elif 'id' in response:
            return response['id']
        else:
            raise Exception(f"Could not extract task_id from response: {response}")
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get status of an async task"""
        endpoints_to_try = [
            f"/v1/ai/mystic/{task_id}",
            f"/v1/ai/image-upscaler/{task_id}",
            f"/v1/ai/task/{task_id}",
            f"/v1/task/{task_id}"
        ]
        
        last_error = None
        for endpoint in endpoints_to_try:
            try:
                response = self.get(endpoint)
                print(f"🔍 DEBUG - Raw API response from {endpoint}: {response}")
                return response
            except Exception as e:
                last_error = e
                continue
        
        raise last_error
    
    def download_image(self, url: str) -> bytes:
        """
        Download image from URL
        
        Args:
            url: Image URL
            
        Returns:
            Image bytes
        """
        try:
            response = self.session.get(url, timeout=60)
            response.raise_for_status()
            return response.content
        except Exception as e:
            raise Exception(f"Failed to download image: {str(e)}")
    
    def get_balance(self) -> Dict[str, Any]:
        """Get current credit balance (if API supports it)"""
        # This endpoint may vary, adjust as needed
        try:
            return self.get("/v1/user/balance")
        except:
            return {"credits": "unknown", "error": "Balance endpoint not available"}


# Convenience function for testing
def test_connection(api_key: str) -> bool:
    """Test if API key is valid"""
    try:
        client = FreepikAPIClient(api_key)
        # Try a simple GET request
        client.get("/v1/ai/loras")  # Public endpoint
        return True
    except:
        return False
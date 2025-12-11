"""
Task Manager for Freepik API
Handles async task polling and result retrieval
"""

import time
from typing import Dict, Any, Optional, Callable
from PIL import Image
import io
from .client import FreepikAPIClient


class FreepikTaskManager:
    """Manages async task execution and polling"""
    
    def __init__(self, client: Optional[FreepikAPIClient] = None):
        self.client = client or FreepikAPIClient()
        
    def set_client(self, client: FreepikAPIClient):
        """Set or update API client"""
        self.client = client
    
    def execute_and_wait(
        self,
        endpoint: str,
        params: Dict[str, Any],
        files: Optional[Dict] = None,
        max_wait: int = 300,
        poll_interval: int = 2,
        progress_callback: Optional[Callable] = None
    ) -> Image.Image:
        """
        Execute task and wait for completion
        
        Args:
            endpoint: API endpoint (e.g., '/v1/ai/mystic')
            params: Task parameters
            files: Optional files for upload
            max_wait: Maximum wait time in seconds
            poll_interval: Seconds between status checks
            progress_callback: Optional callback for progress updates
            
        Returns:
            PIL Image object
        """
        # Create task
        print(f"🚀 Creating task: {endpoint}")
        task_id = self.client.create_task(endpoint, params, files)
        print(f"✓ Task created: {task_id}")
        
        # Poll for completion
        start_time = time.time()
        elapsed = 0
        
        while elapsed < max_wait:
            # Get status
            status_response = self.client.get_task_status(task_id)
            status = self._parse_status(status_response)
            
            elapsed = int(time.time() - start_time)
            
            # Progress callback
            if progress_callback:
                progress_callback(status, elapsed, max_wait)
            
            print(f"⏳ Status: {status['state']} | Elapsed: {elapsed}s")
            
            # Check status
            if status['state'] in ['success', 'completed']:
                print(f"✅ Task completed in {elapsed}s")
                return self._download_result(status)
            
            elif status['state'] == 'failed':
                error_msg = status.get('error', 'Unknown error')
                raise Exception(f"❌ Task failed: {error_msg}")
            
            elif status['state'] in ['pending', 'processing', 'queued', 'created', 'in_progress']:
                time.sleep(poll_interval)
            
            else:
                raise Exception(f"Unknown status: {status['state']}")
        
        raise TimeoutError(f"Task timeout after {max_wait}s")
    
    def _parse_status(self, response: Dict) -> Dict[str, Any]:
        """Parse task status from different API response formats"""
    
        # Handle Freepik's nested data structure
        if 'data' in response:
            data = response['data']
            status = data.get('status', '').lower()
        
        # Map Freepik status to our internal format
        state_map = {
            'created': 'created',
            'in_progress': 'in_progress',
            'completed': 'completed',
            'failed': 'failed',
            'error': 'failed'
        }
        
        parsed = {
            'state': state_map.get(status, status),
            'output_url': None,
            'error': None
        }
        
        # Extract image URL from 'generated' array
        if 'generated' in data and data['generated']:
            parsed['output_url'] = data['generated'][0]
        
        # Extract error if present
        if 'error' in data:
            parsed['error'] = data.get('error')
            
        return parsed
    
        # Fallback for other formats
        return {
            'state': response.get('status', 'unknown').lower(),
            'output_url': response.get('result') or response.get('output_url'),
            'error': response.get('error')
    }
    
    def _download_result(self, status: Dict[str, str]) -> Image.Image:
        """Download and return result image"""
        output_url = status.get('output_url')
        
        if not output_url:
            print(f"🔍 DEBUG - Full response: {status}")
            raise Exception("No output URL in successful task")
        
        # Handle multiple outputs (array)
        if isinstance(output_url, list):
            output_url = output_url[0]  # Take first result
        
        # Handle object with url property
        if isinstance(output_url, dict):
            output_url = output_url.get('url', output_url.get('image_url'))
        
        print(f"⬇️ Downloading result from: {output_url}")
        
        # Download image
        image_bytes = self.client.download_image(output_url)
        
        # Convert to PIL Image
        image = Image.open(io.BytesIO(image_bytes))
        
        print(f"✓ Image downloaded: {image.size}")
        return image
    
    def execute_batch(
        self,
        endpoint: str,
        params_list: list,
        max_wait: int = 300,
        max_concurrent: int = 3
    ) -> list:
        """
        Execute multiple tasks with concurrency limit
        
        Args:
            endpoint: API endpoint
            params_list: List of parameter dicts
            max_wait: Max wait per task
            max_concurrent: Max concurrent tasks
            
        Returns:
            List of PIL Images
        """
        results = []
        
        # Simple sequential implementation for now
        # TODO: Implement proper concurrent execution with limit
        for i, params in enumerate(params_list):
            print(f"\n📦 Batch task {i+1}/{len(params_list)}")
            try:
                result = self.execute_and_wait(endpoint, params, max_wait=max_wait)
                results.append(result)
            except Exception as e:
                print(f"❌ Batch task {i+1} failed: {str(e)}")
                results.append(None)
        
        return results
    
    def get_task_info(self, endpoint: str, task_id: str) -> Dict[str, Any]:
        """Get detailed task information"""
        return self.client.get_task_status(endpoint, task_id)


class ProgressTracker:
    """Simple progress tracking for ComfyUI"""
    
    def __init__(self):
        self.last_update = 0
        
    def __call__(self, status: Dict, elapsed: int, max_wait: int):
        """Progress callback"""
        # Update every 5 seconds
        if elapsed - self.last_update >= 5:
            progress_pct = (elapsed / max_wait) * 100
            print(f"📊 Progress: {progress_pct:.1f}% | State: {status['state']}")
            self.last_update = elapsed

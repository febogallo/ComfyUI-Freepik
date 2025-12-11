"""
Freepik Remove Background Node
Quick background removal utility
"""

import torch
import sys
import os
import io
from PIL import Image

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from ...api.client import FreepikAPIClient
from ...utils.image_utils import pil2tensor, tensor2pil, create_error_image
from ...utils.cache import get_cache


class FreepikRemoveBackground:
    """
    Remove background from images using AI
    Fast and reliable background removal
    """
    
    def __init__(self):
        self.client = None
        self.cache = get_cache()
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_key": ("STRING", {
                    "default": "",
                    "multiline": False
                }),
                "image": ("IMAGE",),
                "use_cache": ("BOOLEAN", {
                    "default": True
                }),
            }
        }
    
    RETURN_TYPES = ("IMAGE", "MASK", "STRING")
    RETURN_NAMES = ("image_no_bg", "mask", "info")
    FUNCTION = "remove_bg"
    CATEGORY = "Freepik/Utilities"
    
    def remove_bg(self, api_key, image, use_cache):
        """Remove background from image"""
        try:
            # Initialize client
            if self.client is None or self.client.api_key != api_key:
                self.client = FreepikAPIClient(api_key)
            
            # Convert tensor to PIL
            pil_image = tensor2pil(image)
            input_size = pil_image.size
            
            print(f"\n✂️ Removing background")
            print(f"   Input size: {input_size}")
            
            # Save image to bytes for multipart upload
            img_byte_arr = io.BytesIO()
            pil_image.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            
            # Build cache key (use image hash)
            import hashlib
            img_hash = hashlib.md5(img_byte_arr.getvalue()).hexdigest()
            cache_key = {"operation": "remove_bg", "image_hash": img_hash}
            
            # Check cache
            if use_cache:
                cached = self.cache.get_cached(cache_key)
                if cached:
                    print("✓ Using cached result")
                    # Extract mask from alpha channel
                    if cached.mode == 'RGBA':
                        mask = cached.split()[3]
                        mask_tensor = pil2tensor(mask.convert('RGB'))
                    else:
                        mask_tensor = torch.ones((1, cached.size[1], cached.size[0], 1))
                    
                    return (pil2tensor(cached), mask_tensor, "cached")
            
            # Prepare multipart file upload
            img_byte_arr.seek(0)
            files = {
                'image_file': ('image.png', img_byte_arr, 'image/png')
            }
            
            # This is a synchronous endpoint (returns immediately)
            response = self.client.post(
                endpoint="/v1/ai/beta/remove-background",
                data={},  # Empty data, everything in files
                files=files
            )
            
            # Extract result URL from response (try multiple fields)
            output_url = None
            if 'high_resolution' in response:
                output_url = response['high_resolution']
            elif 'url' in response:
                output_url = response['url']
            elif 'data' in response:
                if 'high_resolution' in response['data']:
                    output_url = response['data']['high_resolution']
                elif 'url' in response['data']:
                    output_url = response['data']['url']
            
            if not output_url:
                raise Exception(f"No output URL in response: {response}")
            
            # Download result
            print(f"⬇️ Downloading result from: {output_url}")
            result_bytes = self.client.download_image(output_url)
            result_image = Image.open(io.BytesIO(result_bytes))
            
            # Save to cache
            if use_cache:
                self.cache.save_to_cache(cache_key, result_image, {
                    "operation": "remove_background"
                })
            
            # Extract mask from alpha channel
            if result_image.mode == 'RGBA':
                mask = result_image.split()[3]
                mask_tensor = pil2tensor(mask.convert('RGB'))
            else:
                # No alpha, create full mask
                mask_tensor = torch.ones((1, result_image.size[1], result_image.size[0], 1))
            
            result_tensor = pil2tensor(result_image.convert('RGB'))
            info = f"success|{input_size}|removed_bg"
            
            print(f"✅ Background removed: {result_image.size}")
            return (result_tensor, mask_tensor, info)
            
        except Exception as e:
            print(f"❌ Remove background error: {str(e)}")
            error_img = create_error_image(512, 512, f"RemoveBG: {str(e)[:30]}")
            error_tensor = pil2tensor(error_img)
            mask_tensor = torch.zeros((1, 512, 512, 1))
            return (error_tensor, mask_tensor, f"error|{str(e)}")


# Node export
NODE_CLASS_MAPPINGS = {
    "FreepikRemoveBackground": FreepikRemoveBackground,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "FreepikRemoveBackground": "✂️ Freepik Remove Background",
}
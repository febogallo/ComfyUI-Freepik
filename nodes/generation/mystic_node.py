"""
Freepik Mystic Node - Photorealistic AI Image Generation
Generate 1K/2K/4K images with LoRA support
"""

import torch
from PIL import Image
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from ...api.client import FreepikAPIClient
from ...api.tasks import FreepikTaskManager, ProgressTracker
from ...utils.image_utils import pil2tensor, create_error_image
from ...utils.cache import get_cache


class FreepikMystic:
    """
    Generate photorealistic images using Freepik Mystic
    Supports 1K, 2K, and 4K resolutions with LoRA styles
    """
    
    def __init__(self):
        self.client = None
        self.task_manager = None
        self.cache = get_cache()
        
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_key": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "Enter your Freepik API key"
                }),
                "prompt": ("STRING", {
                    "default": "modern architectural visualization, luxury interior, photorealistic, 8k, detailed",
                    "multiline": True,
                    "placeholder": "Describe the image you want to generate"
                }),
                "negative_prompt": ("STRING", {
                    "default": "blurry, low quality, distorted, ugly, bad anatomy",
                    "multiline": True,
                    "placeholder": "Describe what you don't want"
                }),
                "resolution": (["1k", "2k", "4k"], {
                    "default": "2k"
                }),
                "aspect_ratio": ([
                    "square_1_1",
                    "widescreen_16_9",
                    "social_story_9_16",
                    "classic_4_3",
                    "traditional_3_4",
                    "standard_3_2",
                    "portrait_2_3",
                    "horizontal_2_1",
                    "vertical_1_2",
                    "social_5_4",
                    "social_post_4_5",
                    "smartphone_horizontal_20_9",
                    "smartphone_vertical_9_20"
                ], {
                    "default": "widescreen_16_9"
                }),
                "num_images": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 4,
                    "step": 1
                }),
                "guidance_scale": ("FLOAT", {
                    "default": 7.5,
                    "min": 1.0,
                    "max": 20.0,
                    "step": 0.5,
                    "display": "slider"
                }),
                "seed": ("INT", {
                    "default": -1,
                    "min": -1,
                    "max": 0xffffffffffffffff
                }),
                "use_cache": ("BOOLEAN", {
                    "default": True
                }),
            },
            "optional": {
                "lora_id": ("STRING", {
                    "default": "",
                    "placeholder": "Optional: Enter LoRA ID for custom style"
                }),
                "lora_weight": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.0,
                    "max": 2.0,
                    "step": 0.1,
                    "display": "slider"
                }),
            }
        }
    
    RETURN_TYPES = ("IMAGE", "STRING", "FLOAT")
    RETURN_NAMES = ("image", "task_info", "estimated_cost")
    FUNCTION = "generate"
    CATEGORY = "Freepik/Generation"
    OUTPUT_NODE = False
    
    def generate(self, api_key, prompt, negative_prompt, resolution, 
                 aspect_ratio, num_images, guidance_scale, seed, use_cache,
                 lora_id="", lora_weight=1.0):
        """
        Generate image using Freepik Mystic
        """
        try:
            # Initialize client if needed
            if self.client is None or self.client.api_key != api_key:
                self.client = FreepikAPIClient(api_key)
                self.task_manager = FreepikTaskManager(self.client)
            
            # Build parameters
            params = {
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "num_images": num_images,
                "resolution": resolution,
                "aspect_ratio": aspect_ratio,
            }
            
            # Add optional parameters
            if seed != -1:
                params["seed"] = seed
            
            if lora_id:
                params["lora"] = {
                    "id": lora_id,
                    "weight": lora_weight
                }
            
            # Estimate cost
            cost = self._estimate_cost(resolution, num_images)
            print(f"\n💰 Estimated cost: €{cost:.2f}")
            
            # Check cache
            cache_key_params = {**params, "api": "mystic"}
            
            if use_cache:
                cached_image = self.cache.get_cached(cache_key_params)
                if cached_image is not None:
                    print("✓ Using cached result")
                    image_tensor = pil2tensor(cached_image)
                    task_info = "cached_result"
                    return (image_tensor, task_info, 0.0)
            
            # Execute API call
            print(f"\n🚀 Starting Mystic generation...")
            print(f"   Resolution: {resolution} ({aspect_ratio})")
            print(f"   Images: {num_images}")
            print(f"   Guidance: {guidance_scale}")
            
            progress = ProgressTracker()
            
            result_image = self.task_manager.execute_and_wait(
                endpoint="/v1/ai/mystic",
                params=params,
                max_wait=300,  # 5 minutes timeout
                poll_interval=3,
                progress_callback=progress
            )
            
            # Save to cache
            if use_cache:
                self.cache.save_to_cache(
                    cache_key_params,
                    result_image,
                    extra_metadata={
                        "resolution": resolution,
                        "aspect_ratio": aspect_ratio,
                        "cost": cost
                    }
                )
            
            # Convert to tensor
            image_tensor = pil2tensor(result_image)
            
            task_info = f"success|{resolution}|{aspect_ratio}|{result_image.size}"
            
            print(f"✅ Generation complete: {result_image.size}")
            
            return (image_tensor, task_info, cost)
            
        except Exception as e:
            error_msg = str(e)
            print(f"\n❌ Error in Mystic generation: {error_msg}")
            
            # Return error image
            error_image = create_error_image(512, 512, f"Mystic Error: {error_msg[:50]}")
            image_tensor = pil2tensor(error_image)
            
            task_info = f"error|{error_msg}"
            
            return (image_tensor, task_info, 0.0)
    
    def _convert_resolution(self, resolution: str) -> dict:
        """Convert resolution string to API format"""
        # This is a placeholder - adjust based on actual API requirements
        resolution_map = {
            "1K": {"width": 1024, "height": 1024},
            "2K": {"width": 2048, "height": 2048},
            "4K": {"width": 4096, "height": 4096}
        }
        return resolution_map.get(resolution, resolution_map["2K"])
    
    def _estimate_cost(self, resolution: str, num_images: int) -> float:
        """Estimate generation cost"""
        costs = {
            "1k": 0.05,
            "2k": 0.10,
            "4k": 0.20
        }
        base_cost = costs.get(resolution, 0.10)
        return base_cost * num_images


# Node export
NODE_CLASS_MAPPINGS = {
    "FreepikMystic": FreepikMystic
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "FreepikMystic": "🎨 Freepik Mystic (Text-to-Image)"
}

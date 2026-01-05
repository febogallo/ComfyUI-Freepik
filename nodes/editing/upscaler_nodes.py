"""
Freepik Upscaler Nodes - Creative and Precision modes
Powered by Magnific.ai technology
Updated: Full API parameters support
"""

import torch
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from ...api.client import FreepikAPIClient
from ...api.tasks import FreepikTaskManager, ProgressTracker
from ...utils.image_utils import pil2tensor, tensor2pil, pil2base64, create_error_image
from ...utils.cache import get_cache


class FreepikUpscalerCreative:
    """
    AI Image Upscaler - Creative Mode (Magnific)
    Adds or infers new detail guided by prompts
    Full parameter control matching Magnific.ai platform
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
                    "multiline": False
                }),
                "image": ("IMAGE",),
                "upscale_factor": (["2x", "4x", "8x", "16x"], {
                    "default": "2x"
                }),
                "optimized_for": ([
                    "standard",
                    "portrait_soft",
                    "portrait_hard",
                    "art_illustration",
                    "videogame_assets",
                    "nature_landscapes",
                    "films_photography",
                    "3d_renders",
                    "science_fiction_horror"
                ], {
                    "default": "standard"
                }),
                "engine": ([
                    "automatic",
                    "magnific_illusio",
                    "magnific_sharpy",
                    "magnific_sparkle"
                ], {
                    "default": "automatic"
                }),
                "creativity": ("INT", {
                    "default": 0,
                    "min": -10,
                    "max": 10,
                    "step": 1,
                    "display": "slider"
                }),
                "hdr": ("INT", {
                    "default": 0,
                    "min": -10,
                    "max": 10,
                    "step": 1,
                    "display": "slider"
                }),
                "resemblance": ("INT", {
                    "default": 0,
                    "min": -10,
                    "max": 10,
                    "step": 1,
                    "display": "slider"
                }),
                "fractality": ("INT", {
                    "default": 0,
                    "min": -10,
                    "max": 10,
                    "step": 1,
                    "display": "slider"
                }),
                "prompt": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "Guide the upscaling style (optional)"
                }),
                "use_cache": ("BOOLEAN", {
                    "default": True
                }),
            }
        }
    
    RETURN_TYPES = ("IMAGE", "STRING", "FLOAT")
    RETURN_NAMES = ("upscaled_image", "info", "cost")
    FUNCTION = "upscale"
    CATEGORY = "Freepik/Editing"
    
    def upscale(self, api_key, image, upscale_factor, optimized_for, engine,
                creativity, hdr, resemblance, fractality, prompt, use_cache):
        """Upscale image with creative enhancement using full Magnific parameters"""
        try:
            # Initialize client
            if self.client is None or self.client.api_key != api_key:
                self.client = FreepikAPIClient(api_key)
                self.task_manager = FreepikTaskManager(self.client)
            
            # Convert tensor to PIL
            pil_image = tensor2pil(image)
            input_size = pil_image.size
            
            # Convert to base64 for API
            image_base64 = pil2base64(pil_image)
            
            # Build parameters matching Freepik API exactly
            params = {
                "image": image_base64,
                "scale_factor": upscale_factor,  # API expects "2x", "4x", etc.
                "optimized_for": optimized_for,
                "engine": engine,
                "creativity": creativity,
                "hdr": hdr,
                "resemblance": resemblance,
                "fractality": fractality,
            }
            
            # Only add prompt if not empty
            if prompt and prompt.strip():
                params["prompt"] = prompt.strip()
            
            # Calculate output size for cost estimation
            scale_int = int(upscale_factor.replace('x', ''))
            output_size = (
                input_size[0] * scale_int,
                input_size[1] * scale_int
            )
            cost = self._estimate_cost(input_size, output_size)
            
            print(f"\n🔍 Creative Upscaler (Magnific)")
            print(f"   Input: {input_size}")
            print(f"   Factor: {upscale_factor}")
            print(f"   Output: {output_size}")
            print(f"   Optimized for: {optimized_for}")
            print(f"   Engine: {engine}")
            print(f"   Creativity: {creativity} | HDR: {hdr}")
            print(f"   Resemblance: {resemblance} | Fractality: {fractality}")
            print(f"   Cost: €{cost:.2f}")
            
            # Check cache
            if use_cache:
                cached = self.cache.get_cached(params)
                if cached:
                    print("✓ Using cached result")
                    return (pil2tensor(cached), f"cached|{cached.size}", 0.0)
            
            # Execute upscaling
            progress = ProgressTracker()
            result_image = self.task_manager.execute_and_wait(
                endpoint="/v1/ai/image-upscaler",
                params=params,
                max_wait=600,  # 10 minutes for large upscales
                poll_interval=5,
                progress_callback=progress
            )
            
            # Save to cache
            if use_cache:
                self.cache.save_to_cache(params, result_image, {
                    "mode": "creative",
                    "factor": upscale_factor,
                    "optimized_for": optimized_for,
                    "engine": engine,
                    "cost": cost
                })
            
            result_tensor = pil2tensor(result_image)
            info = f"success|{input_size}→{result_image.size}|{upscale_factor}|{engine}"
            
            print(f"✅ Upscaling complete")
            return (result_tensor, info, cost)
            
        except Exception as e:
            print(f"❌ Upscaler error: {str(e)}")
            error_img = create_error_image(512, 512, f"Upscaler: {str(e)[:30]}")
            return (pil2tensor(error_img), f"error|{str(e)}", 0.0)
    
    def _estimate_cost(self, input_size, output_size):
        """Calculate upscaling cost based on Freepik API pricing tiers"""
        output_area = output_size[0] * output_size[1]
        
        # Official pricing tiers from Freepik API docs
        # Based on output area in pixels
        if output_area <= 1280 * 960:  # 1,228,800 pixels
            return 0.10
        elif output_area <= 2560 * 1920:  # 4,915,200 pixels
            return 0.20
        elif output_area <= 5120 * 3840:  # 19,660,800 pixels
            return 0.40
        elif output_area <= 10000 * 10000:  # 100,000,000 pixels
            return 1.20
        else:
            return 1.60


class FreepikUpscalerPrecision:
    """
    AI Image Upscaler - Precision Mode
    High-fidelity upscaling without hallucinations
    Best for logos, UI, product photos
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
                    "multiline": False
                }),
                "image": ("IMAGE",),
                "upscale_factor": (["2x", "4x", "8x", "16x"], {
                    "default": "2x"
                }),
                "denoise_strength": ("FLOAT", {
                    "default": 0.5,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.1,
                    "display": "slider"
                }),
                "sharpen": ("FLOAT", {
                    "default": 0.5,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.1,
                    "display": "slider"
                }),
                "use_cache": ("BOOLEAN", {
                    "default": True
                }),
            }
        }
    
    RETURN_TYPES = ("IMAGE", "STRING", "FLOAT")
    RETURN_NAMES = ("upscaled_image", "info", "cost")
    FUNCTION = "upscale"
    CATEGORY = "Freepik/Editing"
    
    def upscale(self, api_key, image, upscale_factor, 
                denoise_strength, sharpen, use_cache):
        """Upscale with precision (no hallucinations)"""
        try:
            # Initialize client
            if self.client is None or self.client.api_key != api_key:
                self.client = FreepikAPIClient(api_key)
                self.task_manager = FreepikTaskManager(self.client)
            
            # Convert tensor to PIL
            pil_image = tensor2pil(image)
            input_size = pil_image.size
            
            # Convert to base64
            image_base64 = pil2base64(pil_image)
            
            # Build parameters
            params = {
                "image": image_base64,
                "scale_factor": upscale_factor,
                "denoise": denoise_strength,
                "sharpen": sharpen,
                "mode": "precision"
            }
            
            # Calculate output size
            scale_int = int(upscale_factor.replace('x', ''))
            output_size = (
                input_size[0] * scale_int,
                input_size[1] * scale_int
            )
            cost = self._estimate_cost(input_size, output_size)
            
            print(f"\n🎯 Precision Upscaler")
            print(f"   Input: {input_size}")
            print(f"   Factor: {upscale_factor}")
            print(f"   Output: {output_size}")
            print(f"   Cost: €{cost:.2f}")
            
            # Check cache
            if use_cache:
                cached = self.cache.get_cached(params)
                if cached:
                    print("✓ Using cached result")
                    return (pil2tensor(cached), f"cached|{cached.size}", 0.0)
            
            # Execute upscaling
            progress = ProgressTracker()
            result_image = self.task_manager.execute_and_wait(
                endpoint="/v1/ai/image-upscaler-precision",
                params=params,
                max_wait=600,
                poll_interval=5,
                progress_callback=progress
            )
            
            # Save to cache
            if use_cache:
                self.cache.save_to_cache(params, result_image, {
                    "mode": "precision",
                    "factor": upscale_factor,
                    "cost": cost
                })
            
            result_tensor = pil2tensor(result_image)
            info = f"success|{input_size}→{result_image.size}|{upscale_factor}"
            
            print(f"✅ Precision upscaling complete")
            return (result_tensor, info, cost)
            
        except Exception as e:
            print(f"❌ Precision upscaler error: {str(e)}")
            error_img = create_error_image(512, 512, f"Precision: {str(e)[:30]}")
            return (pil2tensor(error_img), f"error|{str(e)}", 0.0)
    
    def _estimate_cost(self, input_size, output_size):
        """Calculate upscaling cost based on Freepik API pricing tiers"""
        output_area = output_size[0] * output_size[1]
        
        # Official pricing tiers from Freepik API docs
        if output_area <= 1280 * 960:
            return 0.10
        elif output_area <= 2560 * 1920:
            return 0.20
        elif output_area <= 5120 * 3840:
            return 0.40
        elif output_area <= 10000 * 10000:
            return 1.20
        else:
            return 1.60


# Node exports
NODE_CLASS_MAPPINGS = {
    "FreepikUpscalerCreative": FreepikUpscalerCreative,
    "FreepikUpscalerPrecision": FreepikUpscalerPrecision,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "FreepikUpscalerCreative": "🔍 Freepik Upscaler (Creative)",
    "FreepikUpscalerPrecision": "🎯 Freepik Upscaler (Precision)",
}
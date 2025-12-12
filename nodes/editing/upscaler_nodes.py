"""
Freepik Upscaler Nodes - Creative and Precision modes
Powered by Magnific.ai technology
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
    AI Image Upscaler - Creative Mode
    Adds or infers new detail guided by prompts
    Powered by Magnific.ai
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
                "prompt": ("STRING", {
                    "default": "enhance details, improve quality, photorealistic",
                    "multiline": True,
                    "placeholder": "Guide the upscaling style"
                }),
                "creativity": ("FLOAT", {
                    "default": 0.5,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.1,
                    "display": "slider"
                }),
                "detail_level": ("FLOAT", {
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
    
    def upscale(self, api_key, image, upscale_factor, prompt, 
                creativity, detail_level, use_cache):
        """Upscale image with creative enhancement"""
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
            
            # Build parameters
            params = {
                "image": image_base64,
                "scale_factor": upscale_factor,  # Ya viene como "2x", "4x", etc
                "prompt": prompt,
                "creativity": int(creativity * 10),  # Convertir 0.0-1.0 a 0-10
                "detail_level": int(detail_level * 10),  # Convertir 0.0-1.0 a 0-10
                "mode": "creative"
            }
            
            print(f"🔍 DEBUG Upscaler params: scale_factor={upscale_factor}, creativity={int(creativity * 10)}, detail_level={int(detail_level * 10)}")

            # Estimate cost
            scale_int = int(upscale_factor.replace('x', ''))  # "4x" -> 4
            output_size = (
                input_size[0] * scale_int,
                input_size[1] * scale_int
            )
            cost = self._estimate_cost(input_size, output_size)

            print(f"\n🔍 Creative Upscaler")
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
                    "cost": cost
                })
            
            result_tensor = pil2tensor(result_image)
            info = f"success|{input_size}→{result_image.size}|{upscale_factor}"
            
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
            return 0.20  # NOT 0.40!
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
            
            # Build parameters - FIXED: igual que Creative
            params = {
                "image": image_base64,
                "scale_factor": upscale_factor,  # String "2x", "4x", etc
                "denoise_strength": int(denoise_strength * 10),  # 0.0-1.0 → 0-10
                "sharpen": int(sharpen * 10),  # 0.0-1.0 → 0-10
                "mode": "precision"
            }
            
            # Estimate cost
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
                endpoint="/v1/ai/image-upscaler",  # MISMO endpoint que Creative
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
        """Same cost calculation as creative mode"""
        output_area = output_size[0] * output_size[1]
        
        if output_area <= 1280 * 960:
            return 0.10
        elif output_area <= 2560 * 1920:
            return 0.40
        elif output_area <= 5120 * 3840:
            return 1.60
        elif output_area <= 10000 * 10000:
            return 1.20
        else:
            return 2.00


# Node exports
NODE_CLASS_MAPPINGS = {
    "FreepikUpscalerCreative": FreepikUpscalerCreative,
    "FreepikUpscalerPrecision": FreepikUpscalerPrecision,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "FreepikUpscalerCreative": "🔍 Freepik Upscaler (Creative)",
    "FreepikUpscalerPrecision": "🎯 Freepik Upscaler (Precision)",
}
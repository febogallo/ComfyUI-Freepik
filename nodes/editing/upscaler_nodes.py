"""
Freepik Upscaler Nodes - Creative and Precision modes
Powered by Magnific.ai technology
Updated: Full API parameters support + Status Display + Seed System + Confirmation
"""

import torch
import sys
import os
import time
import hashlib
import random
import threading
import uuid

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from ...api.client import FreepikAPIClient
from ...api.tasks import FreepikTaskManager, ProgressTracker
from ...utils.image_utils import pil2tensor, tensor2pil, pil2base64, create_error_image
from ...utils.cache import get_cache

# Try to import ComfyUI's PromptServer for WebSocket events
try:
    from server import PromptServer
    HAS_SERVER = True
except ImportError:
    HAS_SERVER = False
    print("[Freepik] Warning: PromptServer not available, status updates disabled")

# Global storage for confirmation responses
_confirmation_responses = {}
_confirmation_lock = threading.Lock()


def send_status_event(node_id, event, **kwargs):
    """Send status event to frontend via WebSocket"""
    if not HAS_SERVER:
        return

    try:
        data = {
            "node_id": node_id,
            "event": event,
            **kwargs
        }
        PromptServer.instance.send_sync("freepik-status", data)
    except Exception as e:
        print(f"[Freepik] Failed to send status event: {e}")


def request_confirmation(node_id, operation, estimated_cost, output_size):
    """Request user confirmation before executing API call"""
    if not HAS_SERVER:
        return True  # Auto-confirm if server not available

    request_id = str(uuid.uuid4())

    # Send confirmation request to frontend
    try:
        PromptServer.instance.send_sync("freepik-confirm", {
            "node_id": node_id,
            "request_id": request_id,
            "operation": operation,
            "estimated_cost": estimated_cost,
            "output_size": output_size
        })
    except Exception as e:
        print(f"[Freepik] Failed to send confirmation request: {e}")
        return True  # Auto-confirm on error

    # Wait for response (max 60 seconds)
    start_time = time.time()
    while time.time() - start_time < 60:
        with _confirmation_lock:
            if request_id in _confirmation_responses:
                confirmed = _confirmation_responses.pop(request_id)
                return confirmed
        time.sleep(0.1)

    print("[Freepik] Confirmation timeout, cancelling")
    return False


def handle_confirmation_response(request_id, confirmed):
    """Handle confirmation response from frontend"""
    with _confirmation_lock:
        _confirmation_responses[request_id] = confirmed


# Register confirmation endpoint if server available
if HAS_SERVER:
    try:
        from aiohttp import web

        @PromptServer.instance.routes.post("/freepik/confirm_response")
        async def confirm_response_handler(request):
            data = await request.json()
            request_id = data.get("request_id")
            confirmed = data.get("confirmed", False)

            if request_id:
                handle_confirmation_response(request_id, confirmed)

            return web.json_response({"status": "ok"})

        print("[Freepik] Confirmation endpoint registered")
    except Exception as e:
        print(f"[Freepik] Failed to register confirmation endpoint: {e}")


def generate_seed():
    """Generate a random seed"""
    return random.randint(0, 2**31 - 1)


def compute_params_hash(params, seed):
    """Compute a hash of parameters including seed for cache key"""
    # Create a copy without the image (too large)
    params_for_hash = {k: v for k, v in params.items() if k != "image"}
    params_for_hash["_seed"] = seed

    # Sort and serialize
    import json
    serialized = json.dumps(params_for_hash, sort_keys=True)
    return hashlib.md5(serialized.encode()).hexdigest()[:16]


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
        self.node_id = None

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
                    "soft_portraits",
                    "hard_portraits",
                    "art_n_illustration",
                    "videogame_assets",
                    "nature_n_landscapes",
                    "films_n_photography",
                    "3d_renders",
                    "science_fiction_n_horror"
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
                    "multiline": False
                }),
                "seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 2**31 - 1,
                    "step": 1,
                    "control_after_generate": True,
                    "display": "number"
                }),
                "confirm_before_run": ("BOOLEAN", {
                    "default": False
                }),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID"
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING", "FLOAT", "INT")
    RETURN_NAMES = ("upscaled_image", "info", "cost", "seed")
    FUNCTION = "upscale"
    CATEGORY = "Freepik/Editing"

    # Mapping from old parameter values to new API values
    OPTIMIZED_FOR_MAP = {
        # Old values -> New API values
        "portrait_soft": "soft_portraits",
        "portrait_hard": "hard_portraits",
        "art_illustration": "art_n_illustration",
        "nature_landscapes": "nature_n_landscapes",
        "films_photography": "films_n_photography",
        "science_fiction_horror": "science_fiction_n_horror",
        # New values (pass through)
        "standard": "standard",
        "soft_portraits": "soft_portraits",
        "hard_portraits": "hard_portraits",
        "art_n_illustration": "art_n_illustration",
        "videogame_assets": "videogame_assets",
        "nature_n_landscapes": "nature_n_landscapes",
        "films_n_photography": "films_n_photography",
        "3d_renders": "3d_renders",
        "science_fiction_n_horror": "science_fiction_n_horror",
    }

    def upscale(self, api_key, image, upscale_factor, optimized_for, engine,
                creativity, hdr, resemblance, fractality, prompt,
                seed, confirm_before_run, unique_id=None):
        """Upscale image with creative enhancement using full Magnific parameters"""

        # Get node ID for status updates (unique_id is provided by ComfyUI)
        self.node_id = unique_id if unique_id else id(self)

        try:
            # Seed is handled automatically by ComfyUI's control_after_generate
            current_seed = seed

            # Initialize client
            if self.client is None or self.client.api_key != api_key:
                self.client = FreepikAPIClient(api_key)
                self.task_manager = FreepikTaskManager(self.client)

            # Convert tensor to PIL
            pil_image = tensor2pil(image)
            input_size = pil_image.size

            # Convert to base64 for API
            image_base64 = pil2base64(pil_image)

            # Compute image hash for cache (using first 1000 chars of base64)
            image_hash = hashlib.md5(image_base64[:1000].encode()).hexdigest()[:8]

            # Apply mapping for old parameter values (backwards compatibility)
            optimized_for_api = self.OPTIMIZED_FOR_MAP.get(optimized_for, optimized_for)

            # Build parameters matching Freepik API exactly
            params = {
                "image": image_base64,
                "scale_factor": upscale_factor,
                "optimized_for": optimized_for_api,
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

            # Compute cache key including seed and image hash
            cache_key_params = {
                "image_hash": image_hash,
                "scale_factor": upscale_factor,
                "optimized_for": optimized_for_api,
                "engine": engine,
                "creativity": creativity,
                "hdr": hdr,
                "resemblance": resemblance,
                "fractality": fractality,
                "prompt": prompt.strip() if prompt else "",
                "seed": current_seed
            }

            # Send estimate event
            send_status_event(self.node_id, "estimate", estimated_cost=cost)

            print(f"\n[Freepik] Creative Upscaler (Magnific)")
            print(f"   Input: {input_size}")
            print(f"   Factor: {upscale_factor}")
            print(f"   Output: {output_size}")
            print(f"   Seed: {current_seed}")
            print(f"   Optimized for: {optimized_for} -> {optimized_for_api}")
            print(f"   Engine: {engine}")
            print(f"   Creativity: {creativity} | HDR: {hdr}")
            print(f"   Resemblance: {resemblance} | Fractality: {fractality}")
            print(f"   Estimated Cost: EUR {cost:.2f}")

            # Check cache first
            cached = self.cache.get_cached(cache_key_params)
            if cached:
                print("[Freepik] Using cached result")
                send_status_event(self.node_id, "cached")
                return (pil2tensor(cached), f"cached|{cached.size}|seed:{current_seed}", 0.0, current_seed)

            # Request confirmation if enabled
            if confirm_before_run:
                send_status_event(self.node_id, "start",
                                  estimated_cost=cost,
                                  message="Waiting for confirmation...")

                confirmed = request_confirmation(
                    self.node_id,
                    f"Creative Upscale {upscale_factor}",
                    cost,
                    f"{output_size[0]}x{output_size[1]}"
                )

                if not confirmed:
                    print("[Freepik] User cancelled operation")
                    send_status_event(self.node_id, "error", message="Cancelled by user")
                    error_img = create_error_image(512, 512, "Cancelled")
                    return (pil2tensor(error_img), "cancelled|user", 0.0, current_seed)

            # Send start event
            send_status_event(self.node_id, "start",
                              estimated_cost=cost,
                              message="Starting upscale...")

            # Execute upscaling with progress callback
            def progress_callback(status, elapsed, max_wait):
                send_status_event(self.node_id, "polling",
                                  api_status=status.get('state', 'processing'),
                                  elapsed=elapsed)

            send_status_event(self.node_id, "processing",
                              message="Uploading to Freepik...",
                              estimated_cost=cost)

            result_image = self.task_manager.execute_and_wait(
                endpoint="/v1/ai/image-upscaler",
                params=params,
                max_wait=600,
                poll_interval=5,
                progress_callback=progress_callback
            )

            # Save to cache
            self.cache.save_to_cache(cache_key_params, result_image, {
                "mode": "creative",
                "factor": upscale_factor,
                "optimized_for": optimized_for,
                "engine": engine,
                "seed": current_seed,
                "cost": cost
            })

            result_tensor = pil2tensor(result_image)
            info = f"success|{input_size}->{result_image.size}|{upscale_factor}|{engine}|seed:{current_seed}"

            # Send completion event
            send_status_event(self.node_id, "completed", cost=cost)

            print(f"[Freepik] Upscaling complete")
            return (result_tensor, info, cost, current_seed)

        except Exception as e:
            print(f"[Freepik] Upscaler error: {str(e)}")
            send_status_event(self.node_id, "error", message=str(e)[:50])
            error_img = create_error_image(512, 512, f"Upscaler: {str(e)[:30]}")
            return (pil2tensor(error_img), f"error|{str(e)}", 0.0, seed)

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
        self.node_id = None

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
                "seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 2**31 - 1,
                    "step": 1,
                    "control_after_generate": True,
                    "display": "number"
                }),
                "confirm_before_run": ("BOOLEAN", {
                    "default": False
                }),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID"
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING", "FLOAT", "INT")
    RETURN_NAMES = ("upscaled_image", "info", "cost", "seed")
    FUNCTION = "upscale"
    CATEGORY = "Freepik/Editing"

    def upscale(self, api_key, image, upscale_factor,
                denoise_strength, sharpen, seed, confirm_before_run, unique_id=None):
        """Upscale with precision (no hallucinations)"""

        self.node_id = unique_id if unique_id else id(self)

        try:
            # Seed is handled automatically by ComfyUI's control_after_generate
            current_seed = seed

            # Initialize client
            if self.client is None or self.client.api_key != api_key:
                self.client = FreepikAPIClient(api_key)
                self.task_manager = FreepikTaskManager(self.client)

            # Convert tensor to PIL
            pil_image = tensor2pil(image)
            input_size = pil_image.size

            # Convert to base64
            image_base64 = pil2base64(pil_image)

            # Compute image hash for cache
            image_hash = hashlib.md5(image_base64[:1000].encode()).hexdigest()[:8]

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

            # Cache key params
            cache_key_params = {
                "image_hash": image_hash,
                "scale_factor": upscale_factor,
                "denoise": denoise_strength,
                "sharpen": sharpen,
                "mode": "precision",
                "seed": current_seed
            }

            # Send estimate event
            send_status_event(self.node_id, "estimate", estimated_cost=cost)

            print(f"\n[Freepik] Precision Upscaler")
            print(f"   Input: {input_size}")
            print(f"   Factor: {upscale_factor}")
            print(f"   Output: {output_size}")
            print(f"   Seed: {current_seed}")
            print(f"   Estimated Cost: EUR {cost:.2f}")

            # Check cache
            cached = self.cache.get_cached(cache_key_params)
            if cached:
                print("[Freepik] Using cached result")
                send_status_event(self.node_id, "cached")
                return (pil2tensor(cached), f"cached|{cached.size}|seed:{current_seed}", 0.0, current_seed)

            # Request confirmation if enabled
            if confirm_before_run:
                send_status_event(self.node_id, "start",
                                  estimated_cost=cost,
                                  message="Waiting for confirmation...")

                confirmed = request_confirmation(
                    self.node_id,
                    f"Precision Upscale {upscale_factor}",
                    cost,
                    f"{output_size[0]}x{output_size[1]}"
                )

                if not confirmed:
                    print("[Freepik] User cancelled operation")
                    send_status_event(self.node_id, "error", message="Cancelled by user")
                    error_img = create_error_image(512, 512, "Cancelled")
                    return (pil2tensor(error_img), "cancelled|user", 0.0, current_seed)

            # Send start event
            send_status_event(self.node_id, "start",
                              estimated_cost=cost,
                              message="Starting upscale...")

            # Execute upscaling with progress callback
            def progress_callback(status, elapsed, max_wait):
                send_status_event(self.node_id, "polling",
                                  api_status=status.get('state', 'processing'),
                                  elapsed=elapsed)

            send_status_event(self.node_id, "processing",
                              message="Uploading to Freepik...",
                              estimated_cost=cost)

            result_image = self.task_manager.execute_and_wait(
                endpoint="/v1/ai/image-upscaler-precision",
                params=params,
                max_wait=600,
                poll_interval=5,
                progress_callback=progress_callback
            )

            # Save to cache
            self.cache.save_to_cache(cache_key_params, result_image, {
                "mode": "precision",
                "factor": upscale_factor,
                "seed": current_seed,
                "cost": cost
            })

            result_tensor = pil2tensor(result_image)
            info = f"success|{input_size}->{result_image.size}|{upscale_factor}|seed:{current_seed}"

            # Send completion event
            send_status_event(self.node_id, "completed", cost=cost)

            print(f"[Freepik] Precision upscaling complete")
            return (result_tensor, info, cost, current_seed)

        except Exception as e:
            print(f"[Freepik] Precision upscaler error: {str(e)}")
            send_status_event(self.node_id, "error", message=str(e)[:50])
            error_img = create_error_image(512, 512, f"Precision: {str(e)[:30]}")
            return (pil2tensor(error_img), f"error|{str(e)}", 0.0, seed)

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
    "FreepikUpscalerCreative": "Freepik Upscaler (Creative)",
    "FreepikUpscalerPrecision": "Freepik Upscaler (Precision)",
}

"""
ComfyUI-Freepik Custom Node
Integrate Freepik API into ComfyUI workflows
Author: Felipe
Version: 0.1.0
"""

from .nodes.generation.mystic_node import FreepikMystic
from .nodes.editing.upscaler_nodes import FreepikUpscalerCreative, FreepikUpscalerPrecision
from .nodes.utilities.remove_bg_node import FreepikRemoveBackground

# Node mappings for ComfyUI
NODE_CLASS_MAPPINGS = {
    "FreepikMystic": FreepikMystic,
    "FreepikUpscalerCreative": FreepikUpscalerCreative,
    "FreepikUpscalerPrecision": FreepikUpscalerPrecision,
    "FreepikRemoveBackground": FreepikRemoveBackground,
}

# Display names in ComfyUI menu
NODE_DISPLAY_NAME_MAPPINGS = {
    "FreepikMystic": "Freepik Mystic (Text-to-Image)",
    "FreepikUpscalerCreative": "Freepik Upscaler Creative",
    "FreepikUpscalerPrecision": "Freepik Upscaler Precision",
    "FreepikRemoveBackground": "Freepik Remove Background",
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']

print("✓ ComfyUI-Freepik nodes loaded successfully")

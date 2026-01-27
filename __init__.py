"""
ComfyUI-Freepik Custom Node
Integrate Freepik API into ComfyUI workflows
Author: Felipe
Version: 0.2.0

Features:
- Real-time status display on nodes
- Seed system to prevent duplicate API calls
- Confirmation dialog before expensive operations
"""

import os

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

# Web directory for JavaScript extensions (status display, confirmations)
WEB_DIRECTORY = "./web"

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']

print("[Freepik] ComfyUI-Freepik v0.2.0 loaded")
print("[Freepik] Features: Status Display, Seed System, Confirmation Mode")

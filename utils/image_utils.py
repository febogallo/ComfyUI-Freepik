"""
Image utilities for ComfyUI-Freepik
Handle conversions between PIL, Tensor, Base64, and file formats
"""

import torch
import numpy as np
from PIL import Image
import base64
import io
from typing import Union, Tuple


def pil2tensor(image: Image.Image) -> torch.Tensor:
    """
    Convert PIL Image to ComfyUI tensor format
    
    Args:
        image: PIL Image
        
    Returns:
        torch.Tensor in [1, H, W, C] format with values in [0, 1]
    """
    # Convert to RGB if needed
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Convert to numpy array
    np_image = np.array(image).astype(np.float32) / 255.0
    
    # Add batch dimension [H, W, C] -> [1, H, W, C]
    tensor = torch.from_numpy(np_image)[None,]
    
    return tensor


def tensor2pil(tensor: torch.Tensor) -> Image.Image:
    """
    Convert ComfyUI tensor to PIL Image
    
    Args:
        tensor: torch.Tensor in [1, H, W, C] or [H, W, C] format
        
    Returns:
        PIL Image
    """
    # Remove batch dimension if present
    if len(tensor.shape) == 4:
        tensor = tensor.squeeze(0)
    
    # Convert to numpy
    np_image = tensor.cpu().numpy()
    
    # Scale to 0-255
    np_image = (np_image * 255).clip(0, 255).astype(np.uint8)
    
    # Convert to PIL
    image = Image.fromarray(np_image, mode='RGB')
    
    return image


def pil2base64(image: Image.Image, format: str = 'PNG') -> str:
    """
    Convert PIL Image to base64 string
    
    Args:
        image: PIL Image
        format: Image format (PNG, JPEG)
        
    Returns:
        Base64 encoded string
    """
    buffered = io.BytesIO()
    image.save(buffered, format=format)
    img_bytes = buffered.getvalue()
    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
    
    return img_base64


def base642pil(base64_string: str) -> Image.Image:
    """
    Convert base64 string to PIL Image
    
    Args:
        base64_string: Base64 encoded image
        
    Returns:
        PIL Image
    """
    # Remove data URI prefix if present
    if ',' in base64_string:
        base64_string = base64_string.split(',')[1]
    
    img_bytes = base64.b64decode(base64_string)
    image = Image.open(io.BytesIO(img_bytes))
    
    return image


def tensor2base64(tensor: torch.Tensor, format: str = 'PNG') -> str:
    """
    Convert tensor to base64 string
    
    Args:
        tensor: ComfyUI tensor
        format: Image format
        
    Returns:
        Base64 encoded string
    """
    image = tensor2pil(tensor)
    return pil2base64(image, format)


def base642tensor(base64_string: str) -> torch.Tensor:
    """
    Convert base64 string to tensor
    
    Args:
        base64_string: Base64 encoded image
        
    Returns:
        ComfyUI tensor
    """
    image = base642pil(base64_string)
    return pil2tensor(image)


def resize_image(
    image: Image.Image,
    target_size: Union[int, Tuple[int, int]],
    maintain_aspect: bool = True
) -> Image.Image:
    """
    Resize image intelligently
    
    Args:
        image: PIL Image
        target_size: Target size as int (max dimension) or (width, height)
        maintain_aspect: Whether to maintain aspect ratio
        
    Returns:
        Resized PIL Image
    """
    if isinstance(target_size, int):
        # Single dimension - resize to fit within max dimension
        max_dim = target_size
        width, height = image.size
        
        if width > height:
            new_width = max_dim
            new_height = int(height * (max_dim / width))
        else:
            new_height = max_dim
            new_width = int(width * (max_dim / height))
        
        target_size = (new_width, new_height)
    
    if maintain_aspect:
        image.thumbnail(target_size, Image.Resampling.LANCZOS)
        return image
    else:
        return image.resize(target_size, Image.Resampling.LANCZOS)


def prepare_image_for_api(
    image: Union[Image.Image, torch.Tensor],
    format: str = 'PNG',
    max_size: int = 4096
) -> Tuple[str, dict]:
    """
    Prepare image for API upload
    
    Args:
        image: PIL Image or tensor
        format: Output format
        max_size: Maximum dimension
        
    Returns:
        (base64_string, metadata_dict)
    """
    # Convert to PIL if needed
    if isinstance(image, torch.Tensor):
        image = tensor2pil(image)
    
    # Resize if too large
    width, height = image.size
    if max(width, height) > max_size:
        image = resize_image(image, max_size, maintain_aspect=True)
        print(f"⚠️ Image resized from {width}x{height} to {image.size}")
    
    # Convert to base64
    base64_string = pil2base64(image, format)
    
    metadata = {
        'original_size': (width, height),
        'processed_size': image.size,
        'format': format,
        'size_bytes': len(base64_string)
    }
    
    return base64_string, metadata


def create_error_image(width: int = 512, height: int = 512, 
                      message: str = "Error") -> Image.Image:
    """Create error placeholder image"""
    from PIL import ImageDraw, ImageFont
    
    image = Image.new('RGB', (width, height), color='#FF0000')
    draw = ImageDraw.Draw(image)
    
    # Draw error message
    try:
        # Try to use default font
        draw.text((10, 10), message, fill='white')
    except:
        pass
    
    return image


def batch_pil2tensor(images: list) -> torch.Tensor:
    """
    Convert list of PIL Images to batched tensor
    
    Args:
        images: List of PIL Images
        
    Returns:
        Batched tensor [B, H, W, C]
    """
    tensors = [pil2tensor(img) for img in images]
    return torch.cat(tensors, dim=0)


def batch_tensor2pil(tensor: torch.Tensor) -> list:
    """
    Convert batched tensor to list of PIL Images
    
    Args:
        tensor: Batched tensor [B, H, W, C]
        
    Returns:
        List of PIL Images
    """
    images = []
    for i in range(tensor.shape[0]):
        image = tensor2pil(tensor[i:i+1])
        images.append(image)
    return images

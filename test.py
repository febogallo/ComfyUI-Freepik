"""
Test script for ComfyUI-Freepik nodes
Run this to verify installation and API connectivity
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.client import FreepikAPIClient, test_connection
from utils.cache import get_cache
from utils.image_utils import create_error_image, pil2tensor

def test_imports():
    """Test that all imports work"""
    print("\n" + "="*60)
    print("🧪 Testing imports...")
    print("="*60)
    
    try:
        from nodes.generation.mystic_node import FreepikMystic
        print("✅ FreepikMystic imported successfully")
        
        from nodes.editing.upscaler_nodes import FreepikUpscalerCreative, FreepikUpscalerPrecision
        print("✅ Upscaler nodes imported successfully")
        
        from nodes.utilities.remove_bg_node import FreepikRemoveBackground
        print("✅ RemoveBackground imported successfully")
        
        return True
    except Exception as e:
        print(f"❌ Import error: {str(e)}")
        return False


def test_cache_system():
    """Test cache functionality"""
    print("\n" + "="*60)
    print("🧪 Testing cache system...")
    print("="*60)
    
    try:
        cache = get_cache()
        print(f"✅ Cache initialized")
        
        cache.print_stats()
        
        # Test cache key generation
        test_params = {
            "prompt": "test image",
            "resolution": "2K"
        }
        
        cache_key = cache._get_cache_key(test_params)
        print(f"✅ Cache key generated: {cache_key[:16]}...")
        
        return True
    except Exception as e:
        print(f"❌ Cache error: {str(e)}")
        return False


def test_api_client(api_key=None):
    """Test API client connectivity"""
    print("\n" + "="*60)
    print("🧪 Testing API client...")
    print("="*60)
    
    if not api_key:
        print("⚠️  No API key provided - skipping connection test")
        print("   To test connection: python test.py YOUR_API_KEY")
        return True
    
    try:
        client = FreepikAPIClient(api_key)
        print("✅ API client initialized")
        
        # Test connection
        print("📡 Testing API connection...")
        result = test_connection(api_key)
        
        if result:
            print("✅ API connection successful!")
        else:
            print("❌ API connection failed - check your key")
        
        return result
    except Exception as e:
        print(f"❌ API client error: {str(e)}")
        return False


def test_image_utils():
    """Test image utility functions"""
    print("\n" + "="*60)
    print("🧪 Testing image utilities...")
    print("="*60)
    
    try:
        # Test error image creation
        error_img = create_error_image(256, 256, "Test")
        print(f"✅ Error image created: {error_img.size}")
        
        # Test PIL to tensor conversion
        tensor = pil2tensor(error_img)
        print(f"✅ PIL→Tensor conversion: {tensor.shape}")
        
        from utils.image_utils import tensor2pil
        back_to_pil = tensor2pil(tensor)
        print(f"✅ Tensor→PIL conversion: {back_to_pil.size}")
        
        return True
    except Exception as e:
        print(f"❌ Image utils error: {str(e)}")
        return False


def test_node_structure():
    """Test node class structure"""
    print("\n" + "="*60)
    print("🧪 Testing node structure...")
    print("="*60)
    
    try:
        from nodes.generation.mystic_node import FreepikMystic
        
        # Check INPUT_TYPES
        inputs = FreepikMystic.INPUT_TYPES()
        print(f"✅ Mystic has {len(inputs['required'])} required inputs")
        print(f"   - {', '.join(inputs['required'].keys())}")
        
        # Check RETURN_TYPES
        print(f"✅ Mystic returns: {FreepikMystic.RETURN_TYPES}")
        
        # Check CATEGORY
        print(f"✅ Mystic category: {FreepikMystic.CATEGORY}")
        
        return True
    except Exception as e:
        print(f"❌ Node structure error: {str(e)}")
        return False


def run_all_tests(api_key=None):
    """Run all tests"""
    print("\n" + "="*60)
    print("🚀 ComfyUI-Freepik Test Suite")
    print("="*60)
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Cache System", test_cache_system()))
    results.append(("Image Utils", test_image_utils()))
    results.append(("Node Structure", test_node_structure()))
    results.append(("API Client", test_api_client(api_key)))
    
    # Summary
    print("\n" + "="*60)
    print("📊 Test Summary")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print("\n" + "="*60)
    print(f"Results: {passed}/{total} tests passed")
    print("="*60)
    
    if passed == total:
        print("\n🎉 All tests passed! ComfyUI-Freepik is ready to use.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check errors above.")
    
    return passed == total


if __name__ == "__main__":
    # Check if API key provided as argument
    api_key = sys.argv[1] if len(sys.argv) > 1 else None
    
    success = run_all_tests(api_key)
    
    sys.exit(0 if success else 1)

# ComfyUI-Freepik Custom Node

Integrate **Freepik API** directly into your ComfyUI workflows. Access powerful AI image generation, upscaling, editing, and video generation tools powered by Freepik and Magnific.ai.

![Version](https://img.shields.io/badge/version-0.1.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## 🚀 Features

### Phase 1: Core Features (Currently Available)

#### Image Generation
- **Freepik Mystic** - Photorealistic AI image generation (1K/2K/4K)
  - LoRA support for custom styles and characters
  - Advanced prompt control
  - Multiple aspect ratios

#### Image Editing
- **Upscaler Creative** - Enhance and stylize with AI-guided detail
- **Upscaler Precision** - High-fidelity upscaling without hallucinations
- **Remove Background** - Quick AI-powered background removal

#### Smart Features
- ✅ Intelligent caching system (avoid redundant API calls)
- ✅ Cost estimation before execution
- ✅ Progress tracking for long operations
- ✅ Automatic retry with exponential backoff

## 📦 Installation

### Method 1: Git Clone (Recommended)

```bash
cd ComfyUI/custom_nodes/
git clone https://github.com/YOUR_USERNAME/ComfyUI-Freepik.git
cd ComfyUI-Freepik
pip install -r requirements.txt
```

### Method 2: Manual Install

1. Download this repository
2. Extract to `ComfyUI/custom_nodes/ComfyUI-Freepik`
3. Install dependencies:
```bash
pip install requests pillow
```

### Method 3: ComfyUI Manager

*(Coming soon - will be added to ComfyUI Manager registry)*

## 🔑 Getting Your API Key

1. Go to [Freepik Developers Dashboard](https://www.freepik.com/developers/dashboard)
2. Create a new application
3. Copy your API key
4. You'll receive **$5 USD in free credits** to get started!

## 🎨 Usage Examples

### Basic Text-to-Image Generation

```
1. Add "Freepik Mystic" node
2. Enter your API key
3. Write your prompt: "modern architectural visualization, luxury interior"
4. Select resolution (2K recommended)
5. Execute!
```

### Upscaling Workflow

```
LoadImage → FreepikUpscalerCreative (4x) → SaveImage
```

### Remove Background + Generation

```
LoadImage → FreepikRemoveBackground → [Your processing] → SaveImage
```

## 💰 Pricing Reference

Based on Freepik API pricing (as of documentation):

| Operation | Cost per Operation |
|-----------|-------------------|
| Mystic 1K | €0.05 |
| Mystic 2K | €0.10 |
| Mystic 4K | €0.20 |
| Upscaler 2x (1K→2K) | €0.10 |
| Upscaler 4x (1K→4K) | €0.40 |
| Relight | €0.10 |
| Style Transfer | €0.10 |
| Remove Background | Variable |

**Note:** All nodes display estimated cost before execution.

## ⚙️ Node Configuration

### Freepik Mystic

**Required:**
- `api_key`: Your Freepik API key
- `prompt`: Text description of desired image
- `resolution`: 1K / 2K / 4K
- `aspect_ratio`: Various ratios supported

**Optional:**
- `lora_id`: Custom LoRA for specific styles
- `lora_weight`: LoRA influence (0.0 - 2.0)
- `seed`: Reproducible results (-1 for random)
- `use_cache`: Enable/disable caching

### Freepik Upscaler Creative

**Required:**
- `api_key`: Your API key
- `image`: Input image tensor
- `upscale_factor`: 2x, 4x, 8x, or 16x
- `prompt`: Guide the enhancement style

**Parameters:**
- `creativity`: 0.0 (faithful) to 1.0 (creative)
- `detail_level`: Amount of detail to add

### Freepik Upscaler Precision

**Use for:**
- Logos and branding
- UI elements
- Product photography
- Technical diagrams

**Best when:** You need exact preservation without "AI artifacts"

## 📊 Cache Management

The cache system saves results locally to avoid redundant API calls:

```python
# View cache stats
from ComfyUI-Freepik.utils.cache import get_cache

cache = get_cache()
cache.print_stats()

# Clear old cache (older than 30 days)
cache.clear_cache(older_than_days=30)

# Clear all cache
cache.clear_cache()
```

**Cache Location:** `ComfyUI-Freepik/cache/`

## 🔧 Troubleshooting

### Common Issues

**"API key not set" error:**
- Make sure you've entered your API key in the node
- Verify key is valid at [Freepik Dashboard](https://www.freepik.com/developers/dashboard)

**"Task timeout" error:**
- Some operations (especially upscaling) can take 5-10 minutes
- Check your internet connection
- Verify you have sufficient API credits

**Import errors:**
- Run `pip install -r requirements.txt`
- Restart ComfyUI completely

**Cache issues:**
- Clear cache: Delete `ComfyUI-Freepik/cache/` folder
- Disable cache: Set `use_cache` to False

## 🗺️ Roadmap

### Phase 2: Video Generation (Coming Soon)
- Kling v2.5 Pro/Std
- PixVerse V5
- Multiple video models
- Image-to-video workflows

### Phase 3: Advanced Features
- Style Transfer
- Image Relight
- Image Expand (outpainting)
- Image-to-Prompt
- Improve Prompt

### Phase 4: Stock Content
- Search Freepik stock library
- Download icons, vectors, photos
- Integration with generation workflows

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Credits

- **Freepik API** - Image generation and editing technology
- **Magnific.ai** - Upscaling technology
- **ComfyUI** - Node-based UI framework
- **Developer:** Felipe @ Pixelflakes

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/YOUR_USERNAME/ComfyUI-Freepik/issues)
- **Freepik API Docs:** [docs.freepik.com](https://docs.freepik.com)
- **Freepik Discord:** [Join Discord](https://discord.com/invite/znXUEBkqM7)

## 🔗 Links

- [Freepik API Homepage](https://www.freepik.com/api)
- [API Documentation](https://docs.freepik.com/introduction)
- [Get API Key](https://www.freepik.com/developers/dashboard)
- [Pricing Information](https://www.freepik.com/api/pricing)

---

**⭐ If this node is useful to you, please star the repository!**

Built with ❤️ for the ComfyUI community

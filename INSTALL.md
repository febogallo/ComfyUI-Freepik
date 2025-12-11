# Quick Installation Guide - ComfyUI-Freepik

## Prerequisites

- ComfyUI installed and working
- Python 3.9+ (same version as your ComfyUI)
- Freepik API key ([Get one here](https://www.freepik.com/developers/dashboard))

## Installation Steps

### 1. Navigate to custom_nodes directory

```bash
cd /path/to/ComfyUI/custom_nodes/
```

### 2. Clone or copy this repository

**Option A: Git Clone**
```bash
git clone https://github.com/YOUR_USERNAME/ComfyUI-Freepik.git
```

**Option B: Manual Install**
- Download this folder
- Copy to `ComfyUI/custom_nodes/ComfyUI-Freepik/`

### 3. Install dependencies

```bash
cd ComfyUI-Freepik
pip install -r requirements.txt
```

**Note:** torch should already be installed with ComfyUI, so the requirements are minimal.

### 4. Restart ComfyUI

Completely restart your ComfyUI server.

### 5. Verify Installation

You should see the following nodes in ComfyUI:

- **Freepik/Generation/**
  - 🎨 Freepik Mystic (Text-to-Image)

- **Freepik/Editing/**
  - 🔍 Freepik Upscaler (Creative)
  - 🎯 Freepik Upscaler (Precision)

- **Freepik/Utilities/**
  - ✂️ Freepik Remove Background

## First Test

### Test 1: Simple Generation

1. Add node: `Freepik Mystic`
2. Enter your API key
3. Prompt: "modern house, architectural visualization"
4. Resolution: 2K
5. Queue prompt
6. Wait ~30-60 seconds
7. You should get a high-quality image!

### Test 2: Upscaling

```
LoadImage → FreepikUpscalerPrecision (2x) → SaveImage
```

## Troubleshooting

### Nodes don't appear in ComfyUI

1. Check ComfyUI console for errors
2. Verify folder structure:
   ```
   ComfyUI/
   └── custom_nodes/
       └── ComfyUI-Freepik/
           ├── __init__.py
           ├── nodes/
           ├── api/
           └── utils/
   ```
3. Restart ComfyUI completely (not just refresh)

### "API key not set" error

- Double-check you entered the key correctly
- Verify key is active at [Freepik Dashboard](https://www.freepik.com/developers/dashboard)

### Import errors

```bash
# Use the same Python as ComfyUI
python -m pip install requests pillow
```

### Cache issues

```bash
# Clear cache if needed
rm -rf ComfyUI-Freepik/cache/
```

## Getting Your API Key

1. Visit [Freepik Developers](https://www.freepik.com/developers/dashboard)
2. Sign in or create account
3. Create new application
4. Copy your API key
5. **You get $5 USD free credits!**

## Configuration

Edit `config.json` to customize:
- Cache settings
- Default parameters
- API timeouts

## Next Steps

- Check the [README.md](README.md) for full documentation
- See example workflows in `/examples` folder (coming soon)
- Join [Freepik Discord](https://discord.com/invite/znXUEBkqM7) for support

## Support

- **Issues:** GitHub Issues
- **Freepik API:** [docs.freepik.com](https://docs.freepik.com)
- **Discord:** [Freepik Community](https://discord.com/invite/znXUEBkqM7)

---

Happy creating! 🎨

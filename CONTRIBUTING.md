# Contributing to ComfyUI-Freepik

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/yourusername/ComfyUI-Freepik/issues)
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - ComfyUI version and environment details
   - Error messages/logs if applicable

### Suggesting Features

1. Check existing [Issues](https://github.com/yourusername/ComfyUI-Freepik/issues) and [Discussions](https://github.com/yourusername/ComfyUI-Freepik/discussions)
2. Create a new issue or discussion with:
   - Clear use case description
   - Proposed solution
   - Alternatives considered

### Pull Requests

1. **Fork** the repository
2. **Create a branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**
4. **Test thoroughly**
5. **Commit** with clear messages:
   ```bash
   git commit -m "Add: Feature description"
   ```
6. **Push** to your fork
7. **Create Pull Request** with:
   - Clear description of changes
   - Link to related issues
   - Screenshots if UI changes

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/ComfyUI-Freepik.git
cd ComfyUI-Freepik

# Install dependencies
pip install -r requirements.txt

# Run tests (when available)
python -m pytest tests/
```

## Code Style

- Follow PEP 8 for Python code
- Use meaningful variable names
- Add docstrings to functions and classes
- Keep functions focused and modular
- Comment complex logic

## Testing

- Test your changes with various scenarios
- Ensure backward compatibility
- Test with different ComfyUI versions if possible
- Check for memory leaks in long-running operations

## Commit Message Guidelines

Use conventional commits format:

- `Add:` New feature
- `Fix:` Bug fix
- `Update:` Update existing functionality
- `Refactor:` Code refactoring
- `Docs:` Documentation changes
- `Test:` Adding or updating tests

Example:
```
Add: Support for 16x upscaling in Creative Upscaler

- Implement 16x factor in upscaler_nodes.py
- Update cost calculation for large outputs
- Add validation for maximum output size
```

## Areas for Contribution

### High Priority
- [ ] Video generation nodes (Kling, PixVerse)
- [ ] Comprehensive test suite
- [ ] Performance optimizations
- [ ] Better error messages

### Medium Priority
- [ ] Additional AI tools (Relight, Style Transfer)
- [ ] Batch processing UI
- [ ] Progress bars in ComfyUI interface
- [ ] Cache management tools

### Documentation
- [ ] More workflow examples
- [ ] Tutorial videos
- [ ] API documentation improvements
- [ ] Troubleshooting guide

## Questions?

- Open a [Discussion](https://github.com/yourusername/ComfyUI-Freepik/discussions)
- Check existing [Issues](https://github.com/yourusername/ComfyUI-Freepik/issues)

## Code of Conduct

- Be respectful and constructive
- Welcome newcomers
- Focus on what is best for the community
- Show empathy towards other community members

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing! 🎉

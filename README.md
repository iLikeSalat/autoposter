# AutoPoster

🤖 Production-ready automated social media posting system with LLM-powered content generation for Threads and Twitter/X.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ Features

- 🤖 **LLM-Powered Content** - Dynamic content generation using OpenAI GPT-4o with persona consistency
- 📸 **Image Support** - Automatic image upload and AI-generated captions
- 🧵 **Multi-Platform** - Simultaneous posting to Threads and Twitter/X
- 💬 **Auto-Reply** - Intelligent comment reply system using LLM
- ⏰ **Smart Scheduling** - Weighted random scheduling for optimal engagement
- 📊 **Rate Limiting** - Built-in safety limits to prevent API issues
- 🔒 **Production-Ready** - Proper logging, error handling, and modular architecture

## 🚀 Quick Start

### Installation

```bash
# Clone or download the project
git clone <repository-url>
cd autoPoster

# Install dependencies
pip install -r requirements.txt
```

### Configuration

1. **Copy example files:**
   ```bash
   cp .env.example .env
   cp config.yaml.example config.yaml
   ```

2. **Edit `.env`** with your API keys:
   ```env
   THREADS_ACCESS_TOKEN=your_token
   THREADS_USER_ID=your_user_id
   OPENAI_API_KEY=your_openai_key
   IMGBB_API_KEY=your_imgbb_key
   ENABLE_AUTO_REPLIES=true
   ```

3. **Get Threads token:**
   ```bash
   python utils/get_threads_token.py
   ```

### Usage

```bash
# Test your setup
python main.py --test

# Run in production mode
python main.py

# Test auto-replies
python tests/test_auto_reply.py
```

## 📁 Project Structure

```
autoposter/
├── src/              # Core modules (posting, LLM, image handling)
├── utils/            # Utility scripts (token generation)
├── tests/            # Test scripts
├── docs/             # Complete documentation
├── images/           # Your image folder
├── data/             # Runtime data (auto-created)
└── logs/             # Log files (auto-created)
```

## 📚 Documentation

- **[Complete Documentation](docs/README.md)** - Full guide with all features
- **[Auto-Reply System](docs/AUTO_REPLY_EXPLANATION.md)** - How auto-replies work
- **[Testing Guide](docs/TESTING_GUIDE.md)** - How to test the system
- **[Troubleshooting](docs/README.md#troubleshooting)** - Common issues and solutions

## 🎯 Key Features

### Content Generation

- **Text Posts**: Generated from story seeds in `stories.txt`
- **Image Captions**: AI-generated based on image analysis and style guides
- **Persona Consistency**: Maintains consistent voice across all content

### Auto-Reply System

- Automatically responds to comments on your posts
- Uses LLM to generate persona-consistent replies
- Respects rate limits (20/day, 3 per thread)
- Filters low-value comments and self-replies

### Smart Scheduling

- Weighted random times (favors active hours)
- Configurable posts per day (default: 10 text + 5 image)
- Avoids low-engagement hours (2-7 AM)

## ⚙️ Configuration

### Environment Variables

See `.env.example` for all available options. Key variables:

- `THREADS_ACCESS_TOKEN` - Your Threads API token
- `OPENAI_API_KEY` - OpenAI API key
- `IMGBB_API_KEY` - Image hosting API key
- `ENABLE_AUTO_REPLIES` - Enable/disable auto-replies

### Config File

Edit `config.yaml` to customize:
- Posting schedule
- LLM model and parameters
- Image folder location
- Platform settings

## 🧪 Testing

```bash
# Test text post
python main.py --test-text

# Test image post
python main.py --test-image

# Test both
python main.py --test

# Test auto-replies
python tests/test_auto_reply.py
```

## 📊 Requirements

- Python 3.8+
- OpenAI API key
- Threads API credentials
- ImgBB API key (for image hosting)

## 🔧 Production Deployment

1. Use a process manager (systemd, PM2, etc.)
2. Set up log rotation
3. Monitor API rate limits
4. Keep `.env` secure (never commit)
5. Use long-lived tokens (60 days)

See [Production Deployment](docs/README.md#production-deployment) for detailed instructions.

## 🐛 Troubleshooting

Common issues and solutions:

- **Permission errors**: Regenerate token with required permissions
- **No comments found**: Post more content, wait for engagement
- **API errors**: Check API keys and rate limits
- **Image upload fails**: Verify ImgBB API key

See [Troubleshooting Guide](docs/README.md#troubleshooting) for more.

## 📝 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions welcome! Please read the documentation first and ensure all tests pass.

## 📖 More Information

For complete documentation, see [docs/README.md](docs/README.md)

---

**Made with ❤️ for automated social media management**

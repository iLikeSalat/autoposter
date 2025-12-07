# AutoPoster - Complete Documentation

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Quick Start](#quick-start)
6. [Project Structure](#project-structure)
7. [Usage Guide](#usage-guide)
8. [Auto-Reply System](#auto-reply-system)
9. [Scheduling](#scheduling)
10. [Content Generation](#content-generation)
11. [Troubleshooting](#troubleshooting)
12. [Production Deployment](#production-deployment)

## Overview

AutoPoster is a production-ready automated social media posting system that uses LLM-powered content generation to create engaging posts for Threads and Twitter/X. It features intelligent scheduling, auto-reply capabilities, and persona-consistent content generation.

## Features

- 🤖 **LLM-Powered Content**: Uses OpenAI GPT-4o for dynamic, persona-consistent content generation
- 📸 **Image Support**: Automatically uploads and posts images with AI-generated captions
- 🧵 **Multi-Platform**: Supports Threads and Twitter/X simultaneously
- 💬 **Auto-Reply**: Intelligent auto-reply system that engages with comments using LLM
- ⏰ **Smart Scheduling**: Weighted random scheduling to maximize engagement
- 📊 **Rate Limiting**: Built-in rate limits to prevent API issues and account suspension
- 🔒 **Production-Ready**: Proper logging, error handling, and configuration management
- 🎯 **Persona Consistency**: Maintains consistent persona across all generated content

## Installation

### Prerequisites

- Python 3.8 or higher
- OpenAI API key
- Threads API credentials
- ImgBB API key (for image hosting)

### Step 1: Clone or Download

```bash
# If using git
git clone <repository-url>
cd autoPoster

# Or download and extract the project
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Set Up Configuration

1. **Copy example files:**
   ```bash
   cp .env.example .env
   cp config.yaml.example config.yaml
   ```

2. **Edit `.env` file** with your API keys and credentials

3. **Edit `config.yaml`** to customize posting schedule and settings

## Configuration

### Environment Variables (.env)

The `.env` file contains all sensitive credentials. See `.env.example` for a template.

**Required:**
- `THREADS_ACCESS_TOKEN` - Long-lived Threads API token
- `THREADS_USER_ID` - Your Threads user ID
- `OPENAI_API_KEY` - OpenAI API key
- `IMGBB_API_KEY` - ImgBB API key for image hosting

**Optional:**
- `ENABLE_THREADS` - Enable/disable Threads (default: true)
- `ENABLE_TWITTER` - Enable/disable Twitter (default: false)
- `ENABLE_AUTO_REPLIES` - Enable auto-reply system (default: false)

### Configuration File (config.yaml)

The `config.yaml` file contains non-sensitive configuration:

- **Schedule**: Posting frequency and timing
- **LLM**: Model selection and parameters
- **Images**: Image folder and upload service
- **Content**: Post length, hashtags, etc.

See `config.yaml.example` for all available options.

### Getting Threads Token

1. Run the token generator:
   ```bash
   python utils/get_threads_token.py
   ```

2. Follow the prompts to authorize the app

3. Copy the generated token to your `.env` file

## Quick Start

### Test Your Setup

```bash
# Test text post
python main.py --test-text

# Test image post
python main.py --test-image

# Test both
python main.py --test

# Test auto-reply system
python tests/test_auto_reply.py
```

### Run in Production Mode

```bash
# Start the auto-poster (runs continuously)
python main.py
```

The bot will:
1. Post an initial thread immediately
2. Continue posting on your configured schedule
3. Check for comments and reply automatically (if enabled)

## Project Structure

```
autoposter/
├── src/                          # Core application modules
│   ├── __init__.py
│   ├── autoposter.py            # Main AutoPoster class
│   ├── config.py                # Configuration management
│   ├── logger.py                # Logging setup
│   ├── threads_poster.py        # Threads API integration
│   ├── threads_reply_manager.py # Reply management & rate limiting
│   ├── llm_content_generator.py # Content generation for posts
│   ├── llm_reply_generator.py   # Reply generation for comments
│   ├── image_fetcher.py         # Image selection from folder
│   ├── image_uploader.py        # Image hosting (ImgBB/Imgur)
│   └── twitter_poster.py        # Twitter/X API integration
├── utils/                        # Utility scripts
│   └── get_threads_token.py     # OAuth token generation
├── tests/                        # Test scripts
│   └── test_auto_reply.py       # Auto-reply testing
├── docs/                         # Documentation
│   ├── README.md                # This file
│   ├── AUTO_REPLY_EXPLANATION.md
│   ├── TESTING_GUIDE.md
│   └── REFACTORING.md
├── images/                       # Image folder (add your images here)
├── data/                         # Runtime data (auto-created)
│   ├── replied_comments.json    # Tracks replied comments
│   └── reply_stats.json         # Reply statistics
├── logs/                         # Log files (auto-created)
│   └── autoposter_YYYYMMDD.log
├── main.py                       # Entry point
├── setup.py                      # Package installation
├── config.yaml.example           # Example configuration
├── .env.example                  # Example environment variables
├── prompts.txt                   # Image caption style guides
├── stories.txt                   # Text post story seeds
└── requirements.txt              # Python dependencies
```

## Usage Guide

### Command Line Options

```bash
python main.py [OPTIONS]

Options:
  --config PATH          Custom config file (default: config.yaml)
  --test                 Test both text and image posts
  --test-text           Test only text post
  --test-image          Test only image post
  --test-replies        Test auto-reply system
  --log-level LEVEL     Set logging level (DEBUG, INFO, WARNING, ERROR)
  -h, --help           Show help message
```

### Examples

```bash
# Normal mode with default config
python main.py

# Use custom config file
python main.py --config production.yaml

# Test mode (posts once and exits)
python main.py --test

# Debug mode with verbose logging
python main.py --log-level DEBUG
```

## Auto-Reply System

The auto-reply system automatically responds to comments on your posts using LLM-generated replies that match your persona.

### How It Works

1. **Checks every 15 minutes** for new comments on your recent posts
2. **Filters comments:**
   - Skips your own comments
   - Skips low-value comments ("lol", "🔥", etc.)
   - Skips already-replied comments
3. **Generates reply** using LLM with your persona
4. **Posts reply** directly to the comment
5. **Tracks replies** to avoid duplicates

### Rate Limits

- **Max 20 replies per day**
- **Max 3 replies per thread**
- **Max 3 replies to same user per thread**
- **2-15 minute random delay** between replies

### Enabling Auto-Replies

1. Set in `.env`:
   ```env
   ENABLE_AUTO_REPLIES=true
   ```

2. Or in `config.yaml`:
   ```yaml
   threads:
     enable_auto_replies: true
   ```

3. Ensure you have `threads_read_replies` and `threads_manage_replies` permissions in your token

### Testing Auto-Replies

```bash
# Test the auto-reply system
python tests/test_auto_reply.py
```

See `docs/AUTO_REPLY_EXPLANATION.md` for detailed information.

## Scheduling

### Weighted Random Scheduling (Recommended)

Posts are scheduled at random times with higher probability during active hours:

- **High activity hours** (higher weight): 9-11 AM, 12-2 PM, 5-9 PM
- **Low activity hours** (lower weight): 8 AM, 3-4 PM, 10-11 PM
- **Avoided hours**: 2-7 AM (never posts)

### Configuration

```yaml
schedule:
  text_posts_per_day: 10
  image_posts_per_day: 5
  random_times: true
  weighted_random: true  # Prioritize active hours
```

### Daily Limits

- **Text posts**: 10 per day (configurable)
- **Image posts**: 5 per day (configurable)
- **Total**: 15 posts per day (safe limit)

## Content Generation

### Text Posts

Text posts are generated from story seeds in `stories.txt`:

- Categories: story, question, hot_take, flirty, vulnerable, etc.
- LLM generates unique posts based on selected seed
- Maintains consistent persona (19-year-old, flirty, validation-seeking)

### Image Posts

Image captions are generated using:

- **Vision analysis**: LLM analyzes the image
- **Style guides**: Prompts from `prompts.txt` guide the tone
- **Persona consistency**: Matches text post persona
- **Engagement questions**: Automatically added if missing

### Customizing Content

1. **Edit `stories.txt`** to add/modify text post seeds
2. **Edit `prompts.txt`** to add/modify image caption styles
3. **Adjust LLM parameters** in `config.yaml`:
   ```yaml
   llm:
     model: "gpt-4o"
     temperature: 0.7  # Higher = more creative
     max_tokens: 500
   ```

## Troubleshooting

### Common Issues

#### "Application does not have permission for this action"

**Solution:** Regenerate your token with the required permissions:
```bash
python utils/get_threads_token.py
```

Make sure the token includes:
- `threads_basic`
- `threads_content_publish`
- `threads_read_replies` (for auto-replies)
- `threads_manage_replies` (for auto-replies)

#### "No unreplied comments found"

**Possible causes:**
- No comments on your posts yet
- All comments already replied to
- Comments filtered out (low-value, self-replies)
- Rate limit reached

**Solution:** Post more content and wait for comments

#### "Failed to generate content"

**Possible causes:**
- OpenAI API key invalid or expired
- API rate limit reached
- Network issues

**Solution:** Check your OpenAI API key and account status

#### Image upload fails

**Possible causes:**
- ImgBB API key invalid
- Image too large
- Network issues

**Solution:** Verify `IMGBB_API_KEY` in `.env`

### Debug Mode

Enable verbose logging:
```bash
python main.py --log-level DEBUG
```

Check log files in `logs/` directory for detailed error messages.

## Production Deployment

### Process Management

Use a process manager to keep the bot running:

**systemd (Linux):**
```ini
[Unit]
Description=AutoPoster
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/autoposter
ExecStart=/usr/bin/python3 /path/to/autoposter/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**PM2 (Node.js process manager):**
```bash
pm2 start main.py --name autoposter --interpreter python3
pm2 save
pm2 startup
```

### Log Rotation

Set up log rotation to prevent disk space issues:

```bash
# Add to /etc/logrotate.d/autoposter
/path/to/autoposter/logs/*.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
}
```

### Security Best Practices

1. **Never commit `.env`** - Already in `.gitignore`
2. **Use long-lived tokens** - Regenerate every 60 days
3. **Monitor API usage** - Check OpenAI and Threads API dashboards
4. **Set up alerts** - Monitor for errors and rate limits
5. **Backup data** - Backup `data/` directory regularly

### Health Checks

Monitor the bot's health:

```bash
# Check if process is running
ps aux | grep main.py

# Check recent logs
tail -f logs/autoposter_$(date +%Y%m%d).log

# Test API connectivity
python main.py --test
```

## Additional Resources

- **Auto-Reply Details**: `docs/AUTO_REPLY_EXPLANATION.md`
- **Testing Guide**: `docs/TESTING_GUIDE.md`
- **Permission Issues**: `docs/FIX_REPLY_PERMISSIONS.md`
- **Refactoring Notes**: `docs/REFACTORING.md`

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review the documentation in `docs/`
3. Check log files for error details
4. Verify all API keys and permissions

## License

MIT License - See LICENSE file for details

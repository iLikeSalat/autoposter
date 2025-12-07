# GitHub Setup Guide

## Quick Setup

### Step 1: Initialize Git Repository

```bash
git init
```

### Step 2: Add All Files

```bash
git add .
```

### Step 3: Create Initial Commit

```bash
git commit -m "Initial commit: Production-ready AutoPoster"
```

### Step 4: Add GitHub Remote

Replace `YOUR_USERNAME` and `YOUR_REPO_NAME` with your actual GitHub username and repository name:

```bash
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
```

Or if using SSH:
```bash
git remote add origin git@github.com:YOUR_USERNAME/YOUR_REPO_NAME.git
```

### Step 5: Push to GitHub

```bash
git branch -M main
git push -u origin main
```

## Complete Example

If your GitHub repository URL is: `https://github.com/username/autoposter`

```bash
# Initialize
git init

# Add files
git add .

# Commit
git commit -m "Initial commit: Production-ready AutoPoster"

# Add remote
git remote add origin https://github.com/username/autoposter.git

# Push
git branch -M main
git push -u origin main
```

## What Gets Pushed

✅ **Included:**
- All source code (`src/`)
- Documentation (`docs/`)
- Configuration examples (`.env.example`, `config.yaml.example`)
- Requirements and setup files
- README and documentation

❌ **Excluded (via .gitignore):**
- `.env` (your actual API keys)
- `config.yaml` (your actual config)
- `data/` (runtime data)
- `logs/` (log files)
- `__pycache__/` (Python cache)
- `used_images.json` (tracking data)

## Verify Before Pushing

Check what will be committed:
```bash
git status
```

Preview what will be pushed:
```bash
git ls-files
```

## Troubleshooting

### "remote origin already exists"
Remove and re-add:
```bash
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
```

### "Authentication failed"
- Use GitHub Personal Access Token instead of password
- Or set up SSH keys
- Or use GitHub CLI: `gh auth login`

### "Permission denied"
- Make sure you have write access to the repository
- Check your GitHub authentication


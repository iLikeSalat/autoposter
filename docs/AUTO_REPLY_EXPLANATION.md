# Auto-Reply System - How It Works

## Which Posts Will It Respond To?

**Only YOUR OWN posts** (threads you posted via the bot).

The system:
1. Fetches your **10 most recent threads** (posts you made)
2. Checks each thread for comments/replies
3. Only responds to comments on **your own content**

It will **NOT** respond to:
- Comments on other people's posts
- Comments on posts you didn't create through the bot
- Your own comments (self-replies)

## Who Will It Respond To?

**Anyone who comments on your posts**, with these filters:

### ✅ Will Respond To:
- Comments from other users on your posts
- Comments that are meaningful (not just "lol", "🔥", etc.)
- Comments that are at least 3 characters long
- Comments from users you haven't already replied to 3+ times on the same thread

### ❌ Will NOT Respond To:
- **Your own comments** (skips self-replies)
- **Low-value comments** like:
  - "lol"
  - "🔥"
  - "❤️"
  - "👍"
  - "yes", "no", "ok"
  - Very short emoji-only comments
- **Comments you already replied to** (tracked in `data/replied_comments.json`)
- **Users you've already replied to 3+ times** on the same thread (to avoid spam)

## How It Works Step-by-Step

### 1. When It Checks
- **Every 15 minutes** when the bot is running
- Or manually via `py test_auto_reply.py` or `py main.py --test-replies`

### 2. What It Does
```
1. Get your 10 most recent threads
   ↓
2. For each thread:
   - Fetch up to 25 comments
   - Filter out:
     * Already replied comments
     * Your own comments
     * Low-value comments
     * Users you've replied to 3+ times
   ↓
3. Take the FIRST eligible comment
   ↓
4. Generate a reply using LLM (Elena's persona)
   ↓
5. Post the reply
   ↓
6. Mark comment as replied
   ↓
7. Wait 2-15 minutes before next reply
```

### 3. Rate Limits (Safety)
- **Max 20 replies per day**
- **Max 3 replies per thread**
- **Max 3 replies to same user per thread**
- **2-15 minute random delay** between replies

## Example Scenario

### Your Post:
```
"I took this pic and idk if it's giving what I think it is... 
would someone older even notice me? be honest"
```

### Comment from User @john_doe:
```
"You look amazing! Would love to chat"
```

### Bot's Response (Generated):
```
"aww thank you! that means a lot coming from someone like you... 
would you actually say hi if you saw me?"
```

## Testing

### To Test:

1. **Post a test thread:**
   ```bash
   py main.py --test-text
   ```

2. **Manually comment on that thread** from another account (or use a different Threads account)

3. **Run the test:**
   ```bash
   py test_auto_reply.py
   ```

The test will show you:
- Which comments it found
- Which comment it will reply to
- The generated reply
- Ask for confirmation before posting

## Important Notes

- **Only responds to YOUR posts** - it won't comment on other people's content
- **One reply at a time** - processes the first eligible comment, then waits
- **Respects all limits** - won't spam or exceed rate limits
- **Tracks everything** - remembers what it replied to in `data/replied_comments.json`
- **Safe content only** - filters out explicit content, slurs, etc.

## Configuration

Enable in `.env`:
```
ENABLE_AUTO_REPLIES=true
```

Or in `config.yaml`:
```yaml
threads:
  enable_auto_replies: true
```


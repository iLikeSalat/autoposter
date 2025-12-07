# Testing Auto-Reply System - Step by Step

## Quick Answer

**For testing, it will respond to:**
- Comments on **posts you made** (via the bot)
- The **first eligible comment** it finds on your most recent posts

## Complete Testing Flow

### Step 1: Post a Test Thread
```bash
py main.py --test-text
```
This creates a post on your Threads account. **Save the post URL or note which post it was.**

### Step 2: Comment on That Post
You need to comment on the post you just created. You can:
- **Option A**: Use a different Threads account to comment
- **Option B**: Use the same account but comment manually from the Threads app/website

**Important**: The comment must be:
- At least 3 characters long
- Not just "lol", "🔥", "yes", "no", etc. (low-value comments are filtered)
- From a different account than the bot (or it will skip your own comments)

### Step 3: Run the Test
```bash
py test_auto_reply.py
```

**What happens:**
1. Script fetches your **10 most recent threads** (posts you made)
2. Looks for comments on those posts
3. Filters out:
   - Comments you already replied to
   - Your own comments
   - Low-value comments ("lol", "🔥", etc.)
   - Users you've replied to 3+ times on the same thread
4. Shows you the **first eligible comment** it found
5. Generates a reply
6. **Asks for confirmation** before posting

### Step 4: Confirm and Post
The script will show:
```
Generated reply: "aww thank you! that means a lot..."
Post this reply? (yes/no):
```

Type `yes` to post, or `no` to cancel.

## Example Test Scenario

### 1. You post:
```
py main.py --test-text
```
Output: `✅ Posted successfully! Post ID: 123456789`

### 2. You (or someone else) comment on that post:
Comment: "You look amazing! Would love to chat"

### 3. You run the test:
```bash
py test_auto_reply.py
```

### 4. Script shows:
```
✓ Found 1 unreplied comment(s)

First Unreplied Comment
Thread ID: 123456789
Reply ID: 987654321
Author: @some_user
Comment: You look amazing! Would love to chat

Generated reply: aww thank you! that means a lot coming from someone like you... 
would you actually say hi if you saw me?

Post this reply? (yes/no):
```

### 5. You type `yes` → Reply is posted!

## Alternative: Quick Test Mode

If you want it to post automatically without asking:

```bash
py main.py --test-replies
```

This does the same thing but **posts automatically** without asking for confirmation.

## Troubleshooting

### "No unreplied comments found"

**Possible reasons:**
1. You haven't commented on your post yet
2. The comment is too short or low-value ("lol", "🔥", etc.)
3. You already replied to that comment
4. The comment is from your own account (it skips self-replies)

**Solution:**
- Make sure you commented from a different account
- Make the comment meaningful (at least 3 characters, not just emojis)
- Check that the post was created successfully

### "Cannot reply now (rate limit reached)"

**Solution:**
- Wait 2-15 minutes between tests
- Or reset the stats in `data/reply_stats.json` (delete the file)

### "Auto-replies are not enabled"

**Solution:**
- Add `ENABLE_AUTO_REPLIES=true` to your `.env` file
- Or set `enable_auto_replies: true` in `config.yaml`

## What Posts Does It Check?

The test script checks your **10 most recent threads** (posts you made via the bot).

It will respond to comments on:
- ✅ Posts you created with `py main.py --test-text`
- ✅ Posts you created with `py main.py --test-image`
- ✅ Posts created during normal bot operation

It will **NOT** respond to:
- ❌ Comments on posts you didn't create through the bot
- ❌ Comments on other people's posts
- ❌ Your own comments

## Summary

**For testing:**
1. Post something → `py main.py --test-text`
2. Comment on it (from another account or manually)
3. Test reply → `py test_auto_reply.py`
4. Confirm → Type `yes` to post

The script will find the comment on your post and reply to it!


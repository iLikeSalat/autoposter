# Fix: "Application does not have permission for this action"

## Problem
The error occurs because your token doesn't have the `threads_read_replies` permission needed to read comments.

## Solution

### Step 1: Regenerate Token with New Permissions

The token generation script has been updated to include the required permissions. You need to regenerate your token:

```bash
py get_threads_token.py
```

This will now request:
- `threads_basic`
- `threads_content_publish`
- `threads_read_replies` ← **NEW** (needed to read comments)
- `threads_manage_replies` ← **NEW** (needed to post replies)

### Step 2: Approve Permissions in Facebook App Dashboard

After regenerating the token, you may need to approve the permissions:

1. Go to: https://developers.facebook.com/apps/
2. Select your Threads app
3. Go to **App Review** → **Permissions and Features**
4. Find these permissions and request approval if needed:
   - `threads_read_replies`
   - `threads_manage_replies`

### Step 3: Update Your .env File

After regenerating the token, update your `.env` file with the new token:

```
THREADS_ACCESS_TOKEN=<new_token_here>
```

### Step 4: Test Again

```bash
py test_auto_reply.py
```

## Important Notes

- **You MUST regenerate the token** - old tokens won't have the new permissions
- **Permissions may need approval** - Check your Facebook App dashboard
- **Long-lived tokens** - The new token will still be long-lived (60 days)

## Verification

After regenerating, you can verify the token has the permissions by checking the token debug info or simply testing the reply system.


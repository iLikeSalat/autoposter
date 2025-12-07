# Imgur Setup for Image Uploads

Threads API requires images to be publicly hosted. This guide shows you how to set up Imgur for automatic image uploads.

## Quick Setup

1. **Get Imgur Client ID**
   - Go to: https://api.imgur.com/oauth2/addclient
   - Log in with your Imgur account (or create one)
   - Select "Anonymous" application type
   - Fill in:
     - App name: `AutoPoster` (or any name)
     - Authorization callback URL: `https://localhost` (not used for anonymous)
     - App website: `https://localhost` (optional)
     - Email: Your email
   - Click "Submit"
   - Copy your **Client ID** (not the Client Secret)

2. **Add to .env file**
   ```
   IMGUR_CLIENT_ID=your_client_id_here
   ```

3. **Done!** The script will automatically upload images to Imgur before posting to Threads.

## How It Works

1. Script selects a random image from your `images/` folder
2. Uploads it to Imgur automatically
3. Gets a public URL
4. Posts to Threads with the image URL

## Alternative: ImgBB

If you prefer ImgBB instead:

1. Get API key from: https://api.imgbb.com/
2. Add to `.env`:
   ```
   IMGUR_CLIENT_ID=your_imgbb_api_key
   ```
3. Update `config.yaml`:
   ```yaml
   images:
     upload_service: "imgbb"
   ```

## Manual Upload Option

If you prefer to upload images manually:

1. Upload all images to Imgur manually
2. Create a file `image_urls.txt` with one URL per line
3. Modify the script to read from this file instead of uploading

Note: The current implementation automatically uploads, which is recommended for convenience.


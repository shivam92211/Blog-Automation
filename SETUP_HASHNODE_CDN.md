# Complete Setup Guide: Hashnode CDN Image Upload

This guide walks you through enabling Hashnode CDN image uploads for your blog automation system.

## Quick Overview

- **Current State**: Images upload to AWS S3 (working)
- **Goal**: Upload images to Hashnode CDN for better integration
- **Requirement**: JWT tokens from browser cookies

## Step-by-Step Setup

### Step 1: Get JWT Tokens from Browser

You need to extract JWT tokens for both Hashnode accounts (Shivam and Gaurav).

#### For Shivam's Account:

1. **Login to Hashnode** as Shivam
   - Go to https://hashnode.com
   - Make sure you're logged in with Shivam's account

2. **Open DevTools**
   - Press `F12` or `Ctrl+Shift+I` (Windows/Linux)
   - Or `Cmd+Option+I` (Mac)

3. **Navigate to Application/Storage Tab**
   - Click "Application" tab (Chrome/Edge) or "Storage" tab (Firefox)
   - In left sidebar, expand "Cookies"
   - Click on "https://hashnode.com"

4. **Copy JWT Token**
   - Find the cookie named `jwt`
   - Double-click its "Value" column
   - Copy the entire value (starts with `eyJ`, about 245 characters)
   - Save it temporarily in a text file

5. **Alternative: Use JavaScript Console**
   ```javascript
   document.cookie.split('; ').find(row => row.startsWith('jwt=')).split('=')[1]
   ```
   Copy the output.

#### For Gaurav's Account:

1. **Logout from Shivam's account**
2. **Login as Gaurav**
3. **Repeat steps 2-4 above**
4. Save Gaurav's JWT token separately

### Step 2: Update .env File

Your `.env` file already has placeholders. Replace them with the actual JWT tokens:

```bash
# Open .env file
nano .env
```

Find these lines:
```bash
HASHNODE_JWT_SHIVAM=your-jwt-token-from-shivam-account-here
HASHNODE_JWT_GAURAV=your-jwt-token-from-gaurav-account-here
```

Replace with your actual tokens:
```bash
HASHNODE_JWT_SHIVAM=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjYwZT...
HASHNODE_JWT_GAURAV=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjYxZj...
```

Save and close the file (`Ctrl+X`, then `Y`, then `Enter` in nano).

### Step 3: Test the Setup

Run the test script to verify everything works:

```bash
source venv/bin/activate
python test_hashnode_cdn_upload.py
```

**Expected output:**
```
INFO:__main__:============================================================
INFO:__main__:HASHNODE CDN UPLOAD TEST
INFO:__main__:============================================================
INFO:__main__:Using API token from publication: Shivam
INFO:__main__:Creating test image...
INFO:__main__:Created test image: /home/shivam/.../test_cover.png
INFO:__main__:Initializing Hashnode CDN service...
INFO:__main__:Uploading image to Hashnode CDN...
INFO:app.services.hashnode_cdn_service:Requesting S3 credentials from Hashnode for .png image (using JWT)
INFO:app.services.hashnode_cdn_service:Successfully received S3 credentials from Hashnode
INFO:app.services.hashnode_cdn_service:Uploading image to S3: /home/shivam/.../test_cover.png
INFO:app.services.hashnode_cdn_service:Successfully uploaded image to S3
INFO:app.services.hashnode_cdn_service:✓ Image uploaded to Hashnode CDN: https://cdn.hashnode.com/res/hashnode/image/upload/...
INFO:__main__:✅ SUCCESS!
INFO:__main__:   CDN URL: https://cdn.hashnode.com/res/hashnode/image/upload/...
```

### Step 4: Run Your Blog Automation

Now run your blog automation normally:

```bash
source venv/bin/activate
python run_blog_automation.py
```

The system will now:
1. Generate blog images
2. Upload to **both** AWS S3 **and** Hashnode CDN
3. Prefer Hashnode CDN URLs when available
4. Fall back to S3 if CDN upload fails

## How It Works

### Image Upload Flow

```
┌─────────────────────┐
│ Generate Image      │
│ (Gemini AI)         │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Upload to S3        │ ✓ Always succeeds
│ (AWS S3)            │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Upload to Hashnode  │ ✓ With JWT token
│ CDN (if JWT avail.) │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Choose Best URL     │
│ 1. Hashnode CDN     │ ← Preferred
│ 2. S3 (fallback)    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Publish to Hashnode │
└─────────────────────┘
```

### Code Changes Made

All code changes are already implemented:

1. ✅ [config/settings.py](config/settings.py) - Reads JWT tokens from env
2. ✅ [app/services/hashnode_cdn_service.py](app/services/hashnode_cdn_service.py) - Uses JWT for authentication
3. ✅ [app/services/image_upload_service.py](app/services/image_upload_service.py) - Supports dual upload
4. ✅ [run_blog_automation.py](run_blog_automation.py) - Passes JWT to services
5. ✅ [.env](.env) - Has JWT placeholders

## Troubleshooting

### Test Fails with 401 Unauthorized

**Problem:**
```
ERROR:app.services.hashnode_cdn_service:HTTP error getting S3 credentials: 401 Client Error: Unauthorized
```

**Solutions:**
1. Make sure you copied the entire JWT token (no spaces)
2. Verify the JWT token is for the correct account
3. Try logging out and back in to get a fresh token
4. Check that you saved the `.env` file properly

### JWT Token Expired

**Symptoms:**
- Was working before, now getting 401 errors
- Token is several weeks/months old

**Solution:**
1. Extract a new JWT token following Step 1
2. Update `.env` with the new token
3. Restart your automation

### Which Account's JWT to Use?

The system automatically matches JWT tokens to publications:
- Shivam's publication → Uses `HASHNODE_JWT_SHIVAM`
- Gaurav's publication → Uses `HASHNODE_JWT_GAURAV`

### Can I Skip This and Use S3 Only?

**Yes!** Your system works perfectly with S3 only. To use S3 only:

1. **Leave JWT tokens empty** in `.env`:
   ```bash
   HASHNODE_JWT_SHIVAM=
   HASHNODE_JWT_GAURAV=
   ```

2. **Optionally change upload mode** in [run_blog_automation.py](run_blog_automation.py:299):
   ```python
   upload_to="s3",  # Changed from "both"
   ```

The automation will:
- ✓ Upload to S3 successfully
- ✗ Skip Hashnode CDN (no JWT)
- ✓ Use S3 URLs for blog posts

## Maintenance

### JWT Token Lifespan

- JWT tokens can expire (typically weeks/months)
- Set a calendar reminder to refresh tokens monthly
- Signs of expiration: 401 errors start appearing

### Refreshing Tokens

When tokens expire:
1. Follow Step 1 again to get new tokens
2. Update `.env` file
3. No code changes needed
4. Restart your automation

### Security Best Practices

1. **Never commit `.env` to git** (already in `.gitignore`)
2. **Keep JWT tokens private** (they grant account access)
3. **Use different tokens for dev/prod** if applicable
4. **Rotate tokens regularly** (monthly recommended)

## Benefits of Using Hashnode CDN

✅ **Native Integration**: Images hosted on Hashnode's own CDN
✅ **Better Performance**: Optimized for Hashnode's platform
✅ **No External Dependencies**: Works even if S3 has issues
✅ **Hashnode Validation**: Passes all Hashnode image requirements
✅ **Automatic Optimization**: Hashnode handles image optimization

## Summary

| Component | Status | Notes |
|-----------|--------|-------|
| S3 Upload | ✅ Working | Always available as fallback |
| Hashnode CDN Upload | ⏳ Needs JWT | Setup required (this guide) |
| Dual Upload | ✅ Implemented | Uploads to both automatically |
| Fallback Logic | ✅ Ready | Uses S3 if CDN fails |

Follow Steps 1-4 above to complete the setup!

# Hashnode CDN Image Upload - Authentication Issue & Workaround

## Problem

When trying to upload images directly to Hashnode's CDN using their `/api/upload-image` endpoint, we encountered a **401 Unauthorized** error.

### Root Cause

The Hashnode `/api/upload-image` endpoint requires **JWT authentication** (from browser cookies), not the **Personal Access Token (PAT)** that is used for their GraphQL API. This JWT token:

- Is obtained by logging into hashnode.com in a browser
- Is stored in browser cookies (specifically the "jwt" cookie)
- Has a shorter lifespan than PATs
- Cannot be easily generated programmatically for automated systems

### Why This Matters

Hashnode's cover image validation error states:
> "Must be an image uploaded to the Hashnode CDN. Please remove and try uploading your image again"

This suggests that Hashnode expects cover images to be hosted on their CDN at URLs like:
```
https://cdn.hashnode.com/res/hashnode/image/upload/...
```

## Current Solution: AWS S3

Currently, the blog automation uploads images to **AWS S3** and uses S3 URLs for cover images. While this works for storing images, Hashnode may not accept these S3 URLs if they enforce CDN-only images in the future or for certain features.

### S3 URLs Look Like:
```
https://blog-automation-phrase-trade.s3.eu-north-1.amazonaws.com/blog-covers/...
```

## Workarounds

### Option 1: Use S3 and Manual Upload (Current Approach)

**Pros:**
- Fully automated
- Works with Personal Access Tokens
- Reliable and scalable
- No manual intervention

**Cons:**
- May not work if Hashnode enforces CDN-only images
- S3 URLs might not pass Hashnode's validation in the UI

**Implementation:**
The current code already does this. Images are uploaded to S3 and the S3 URL is used as the cover image.

### Option 2: JWT Token with Environment Variable

Extract the JWT token from your browser and add it to [.env](.env):

```bash
# Add to .env
HASHNODE_JWT_TOKEN=your-jwt-token-from-browser-cookies
```

**To get your JWT token:**
1. Open hashnode.com in your browser
2. Open DevTools (F12)
3. Go to Application tab → Cookies
4. Copy the value of the "jwt" cookie (245 characters)

**Pros:**
- Enables direct upload to Hashnode CDN
- Uses official CDN URLs

**Cons:**
- JWT tokens expire (need periodic manual renewal)
- Not suitable for fully automated systems
- Security risk if token is compromised

**Implementation:**
Update the `HashnodeCDNService` to accept an optional JWT token parameter.

### Option 3: Hybrid Approach (Recommended)

Upload to both S3 and Hashnode CDN:
- Try Hashnode CDN first (if JWT available)
- Fall back to S3 if Hashnode upload fails
- This provides the best of both worlds

**Implementation:**
The code has been updated to support this via the `upload_to="both"` parameter in `ImageUploadService.upload_and_cleanup()`.

### Option 4: Use Hashnode's Image Uploader in UI

After the blog is published programmatically:
1. Open the draft in Hashnode's editor
2. Upload the cover image manually through their UI
3. Save the draft

**Pros:**
- Guaranteed to work
- Uses official Hashnode CDN

**Cons:**
- Manual step required
- Defeats the purpose of automation

## Code Implementation

### Current Implementation

The code has been updated to support uploading to both S3 and Hashnode CDN:

```python
# In run_blog_automation.py
result = self.image_service.upload_and_cleanup(
    local_path,
    title=topic,
    upload_to="both",  # Upload to both S3 and Hashnode CDN
    hashnode_api_token=api_token
)

# Prefer Hashnode CDN URL, fall back to S3
cdn_url = result.get("hashnode_url") or result.get("s3_url")
```

### If You Have JWT Token

If you want to use JWT authentication:

1. Add JWT to `.env`:
```bash
HASHNODE_JWT_TOKEN=your-jwt-token-here
```

2. Update [config/settings.py](config/settings.py) to read it:
```python
HASHNODE_JWT_TOKEN = os.getenv("HASHNODE_JWT_TOKEN", "")
```

3. Update [app/services/hashnode_cdn_service.py](app/services/hashnode_cdn_service.py):
```python
def __init__(self, api_token: str, jwt_token: Optional[str] = None):
    self.api_token = api_token
    self.jwt_token = jwt_token  # JWT for upload-image endpoint
```

4. Use JWT in the upload request:
```python
# In _get_s3_credentials method
if self.jwt_token:
    # Use JWT token in Cookie header
    headers = {
        "Cookie": f"jwt={self.jwt_token}"
    }
else:
    # Fall back to PAT (may not work)
    headers = {
        "Authorization": self.api_token
    }
```

## Testing

To test the Hashnode CDN upload:

```bash
source venv/bin/activate
python test_hashnode_cdn_upload.py
```

**Expected Results:**
- ❌ Without JWT: Authentication fails (401)
- ✅ With JWT: Upload succeeds, returns CDN URL
- ✅ S3 only: Always works

## Recommendations

1. **Short term:** Continue using S3 URLs (current implementation)
   - Monitor if Hashnode starts rejecting S3 URLs
   - File paths are working in the screenshot you shared

2. **Medium term:** Manually extract JWT token and add to `.env`
   - Update the code to use JWT when available
   - Set up a reminder to refresh JWT token monthly

3. **Long term:** Contact Hashnode support
   - Ask if there's an official way to upload to CDN via API
   - Request PAT support for the upload-image endpoint
   - Suggest they document this in their API docs

## References

- [Hashnode API Documentation](https://apidocs.hashnode.com/)
- [Publish markdown with images to Hashnode via API](https://blog.strajk.me/publish-markdown-with-images-to-hashnode)
- [Using the Hashnode API: A Developer's Guide](https://raajaryan.tech/step-by-step-guide-to-using-the-hashnode-api-for-developers)
- [Utilize Hashnode Public API Possibilities](https://engineering.hashnode.com/what-can-i-do-with-hashnodes-public-api)

## Support

If you continue to see the error "Must be an image uploaded to the Hashnode CDN":
1. Try uploading the image manually in the Hashnode UI
2. Extract the JWT token and add it to your environment
3. Contact Hashnode support for official guidance

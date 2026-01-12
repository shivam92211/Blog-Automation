# Quick Start: Enable Hashnode CDN Upload

## TL;DR - 3 Steps to Enable

### 1. Get JWT Tokens (5 minutes)

**For Shivam's account:**
```bash
# 1. Login to hashnode.com as Shivam
# 2. Press F12 → Application → Cookies → hashnode.com
# 3. Copy the 'jwt' cookie value
# 4. Save it temporarily
```

**For Gaurav's account:**
```bash
# 1. Logout, login as Gaurav
# 2. Repeat steps above
# 3. Save Gaurav's JWT too
```

**Quick method (Console):**
```javascript
document.cookie.split('; ').find(row => row.startsWith('jwt=')).split('=')[1]
```

### 2. Update .env File (1 minute)

```bash
# Edit .env
nano .env
```

Replace these lines:
```bash
HASHNODE_JWT_SHIVAM=eyJhbGci...your-actual-token-here
HASHNODE_JWT_GAURAV=eyJhbGci...your-actual-token-here
```

Save and close (Ctrl+X → Y → Enter).

### 3. Test It (30 seconds)

```bash
source venv/bin/activate
python test_hashnode_cdn_upload.py
```

✅ **Success:** See "Image uploaded to Hashnode CDN"
❌ **Failed:** See troubleshooting below

## That's It!

Your blog automation now uploads to both S3 and Hashnode CDN automatically!

## Troubleshooting Quick Fixes

| Error | Fix |
|-------|-----|
| 401 Unauthorized | Get fresh JWT token, update .env |
| No JWT token provided | Check .env syntax, ensure no extra spaces |
| Token expired | Re-extract JWT from browser |
| Wrong account | Make sure Shivam's JWT goes to SHIVAM variable |

## Want to Skip JWT Setup?

No problem! Your system works great with S3 only:

```bash
# Leave JWT tokens empty in .env
HASHNODE_JWT_SHIVAM=
HASHNODE_JWT_GAURAV=
```

The system will:
- ✅ Upload to S3 (always works)
- ⏭️ Skip Hashnode CDN (gracefully)
- ✅ Use S3 URLs (fully functional)

## Need More Details?

See the complete guides:
- [GET_JWT_TOKEN.md](docs/GET_JWT_TOKEN.md) - Detailed JWT extraction
- [SETUP_HASHNODE_CDN.md](SETUP_HASHNODE_CDN.md) - Full setup guide
- [HASHNODE_CDN_WORKAROUND.md](HASHNODE_CDN_WORKAROUND.md) - Technical details

## Visual Guide

```
Browser (F12)
    ↓
Application Tab
    ↓
Cookies → hashnode.com
    ↓
Copy 'jwt' value
    ↓
Paste in .env
    ↓
Test with test_hashnode_cdn_upload.py
    ↓
✅ Done!
```

## When to Refresh Tokens

Set a monthly reminder to refresh JWT tokens:
- Tokens can expire after weeks/months
- Takes 5 minutes to refresh
- No code changes needed
- Just update .env and restart

---

**Questions?** Check the full documentation or the error logs!

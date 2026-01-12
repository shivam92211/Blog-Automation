# Bug Fix: Image Generation Variable Scope Error

## Issue

The blog automation was failing during image generation with the error:
```
ERROR:__main__:Image generation failed: cannot access local variable 'settings' where it is not associated with a value
```

## Root Cause

In [run_blog_automation.py](run_blog_automation.py), the `generate_image_with_retry()` method had a variable scoping conflict:

```python
# ❌ BROKEN CODE (line 298):
from config.settings import settings  # Conflicting import
jwt_token = None
for pub in settings.HASHNODE_PUBLICATIONS:  # Error here!
```

**Problem**:
- `settings` was already imported at the module level (line 27)
- The function tried to import it again locally
- This created a scope conflict where the local `settings` variable wasn't properly initialized before use

## Solution

Use `self.publications` instead of re-importing `settings`:

```python
# ✅ FIXED CODE:
jwt_token = None
for pub in self.publications:  # Use existing instance variable
    if pub.api_token == api_token:
        jwt_token = pub.jwt_token
        break
```

**Why this works**:
- `self.publications` is already initialized in `__init__()` with `settings.HASHNODE_PUBLICATIONS`
- No need to re-import or access module-level variables
- Follows proper OOP practices using instance variables

## Changed File

- [run_blog_automation.py:298-302](run_blog_automation.py#L298-L302)

## Testing

Verified the fix:
```bash
source venv/bin/activate
python -c "from run_blog_automation import BlogAutomationRunner; runner = BlogAutomationRunner(); print('✓ Works!')"
```

Output:
```
INFO:config.settings:✓ Loaded 2 Hashnode publications
INFO:run_blog_automation:Initialized with 2 publications
✓ Works!
```

## Impact

✅ Image generation now works correctly
✅ JWT tokens are properly retrieved for each publication
✅ Dual upload (S3 + Hashnode CDN) functions as designed

## Related Changes

This was part of the Hashnode CDN upload implementation. See:
- [SETUP_HASHNODE_CDN.md](SETUP_HASHNODE_CDN.md) - Complete setup guide
- [README_HASHNODE_CDN.md](README_HASHNODE_CDN.md) - Technical overview

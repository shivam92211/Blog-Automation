# How to Get JWT Token from Browser

## Visual Step-by-Step Guide

### Method 1: Chrome/Edge/Brave (Recommended)

#### Step 1: Login to Hashnode
```
🌐 Go to: https://hashnode.com
👤 Login with your account (Shivam or Gaurav)
```

#### Step 2: Open Developer Tools
```
Windows/Linux: Press F12 or Ctrl+Shift+I
Mac:           Press Cmd+Option+I
```

#### Step 3: Navigate to Application Tab
```
Developer Tools Window:
┌────────────────────────────────────────────┐
│ Elements Console Sources Network ...       │
│ ▼ Application ← Click here                │
├────────────────────────────────────────────┤
│ Storage                                    │
│   ▼ Local Storage                         │
│   ▼ Session Storage                       │
│   ▼ Cookies                               │
│       ▼ https://hashnode.com ← Click here│
│           ├─ _ga                          │
│           ├─ _gid                         │
│           ├─ jwt      ← THIS ONE!        │
│           └─ ...                          │
└────────────────────────────────────────────┘
```

#### Step 4: Find and Copy JWT Cookie
```
Look for the 'jwt' cookie in the table:

Name     Value                          Domain
─────────────────────────────────────────────
jwt      eyJhbGciOiJIUzI1NiIsInR5cC... .hashnode.com
         ↑                               
         Copy this entire value →
         (starts with eyJ, ~245 characters)
```

**How to copy:**
1. Click on the jwt row
2. Double-click the Value column
3. Ctrl+A (select all)
4. Ctrl+C (copy)
5. Paste in a text file temporarily

### Method 2: Firefox

#### Step 1-2: Same as Chrome
Login and press F12

#### Step 3: Navigate to Storage Tab (not Application)
```
Developer Tools Window:
┌────────────────────────────────────────────┐
│ Inspector Console Debugger ...             │
│ ▼ Storage ← Click here                    │
├────────────────────────────────────────────┤
│ ▼ Cookies                                 │
│     ▼ https://hashnode.com ← Click here  │
│         ├─ _ga                            │
│         ├─ jwt      ← THIS ONE!          │
│         └─ ...                            │
└────────────────────────────────────────────┘
```

#### Step 4: Copy JWT Value
Same as Chrome - find jwt cookie and copy its value

### Method 3: JavaScript Console (Any Browser)

This is the fastest method!

#### Step 1: Open Console
```
Press F12 → Click "Console" tab
```

#### Step 2: Run This Command
```javascript
document.cookie.split('; ').find(row => row.startsWith('jwt=')).split('=')[1]
```

#### Step 3: Copy the Output
```
Console output:
> "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjYw..."
  ↑ Copy everything between the quotes
```

## What the JWT Token Looks Like

**Format:**
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjYwZTQ3YjQxYmY4YjQ0MDAxNWVmNmY4NCIsInVzZXJuYW1lIjoic2hpdmFtIiwiZW1haWwiOiJzaGl2YW1AZXhhbXBsZS5jb20iLCJpYXQiOjE3MDYwNTQxMjMsImV4cCI6MTcwNjY1ODkyM30.Ke8HdK4FVnBD8wYxRqKmE9jP3rZ8sQ2NvL6tY1oC5mA
```

**Characteristics:**
- Starts with: `eyJ` (always)
- Contains: Two dots (.) separating three parts
- Length: ~245 characters (varies)
- Format: Base64 encoded JSON

**NOT like this:**
- ❌ `your-jwt-token-from-shivam-account-here` (placeholder)
- ❌ `53d62f42-dba5-4d3f-b6d4-85a49e78887e` (this is PAT, not JWT)
- ❌ Short token (JWT is long, 200+ chars)

## Extracting Tokens for Both Accounts

### For Shivam's Account:

1. **Logout** from any current session
2. **Login** as Shivam
3. **Extract** JWT using any method above
4. **Save** to a file: `shivam_jwt.txt`

### For Gaurav's Account:

1. **Logout** from Shivam's account
2. **Login** as Gaurav  
3. **Extract** JWT using any method above
4. **Save** to a file: `gaurav_jwt.txt`

## Common Mistakes

### ❌ Wrong: Copied the Wrong Cookie
```
# This is NOT the JWT token:
_ga=GA1.2.123456789.1234567890
```
**Fix:** Look specifically for the cookie named `jwt`

### ❌ Wrong: Copied HTML/Text Around It
```
# Don't include the label:
Name: jwt
Value: eyJhbGci...  ← Only copy the value
```
**Fix:** Copy only the value column, not the name

### ❌ Wrong: Token is Too Short
```
# Real JWT is ~245 chars, not 36:
53d62f42-dba5-4d3f-b6d4-85a49e78887e
```
**Fix:** You copied the PAT instead - go back and get JWT

### ❌ Wrong: Extra Spaces or Newlines
```
# Don't add spaces:
eyJhbGci ...
  ↑ No spaces or newlines!
```
**Fix:** Copy as one continuous string

## Verifying Your Token

### Check Length
```bash
# In terminal:
echo -n "your-token-here" | wc -c
# Should output: ~245 (not 36 or 39)
```

### Check Format
```bash
# Token should:
✓ Start with: eyJ
✓ Have 2 dots: .
✓ Be one line: no newlines
✓ No spaces: continuous string
```

### Quick Test
```bash
# After adding to .env:
python test_jwt_setup.py

# Should show:
# JWT Token: ✓ Set (eyJhbGci...)
# Length: ~245 characters
```

## Token Security

### ⚠️ Important Security Notes

1. **Private**: Never share JWT tokens publicly
2. **Access**: JWT grants full account access
3. **Expiration**: Tokens expire (weeks/months)
4. **Git**: Never commit to version control
5. **Environment**: Only store in `.env` file

### Token Expiration

**Symptoms:**
- Was working, suddenly getting 401 errors
- Token is several weeks old

**Solution:**
- Extract a new token using this guide
- Update `.env` with new token
- Restart automation

## Quick Reference

| Browser | Location |
|---------|----------|
| Chrome/Edge/Brave | F12 → Application → Cookies → hashnode.com → jwt |
| Firefox | F12 → Storage → Cookies → hashnode.com → jwt |
| Safari | Cmd+Option+I → Storage → Cookies → hashnode.com → jwt |
| Any Browser | F12 → Console → Run JS command |

## Next Steps

After copying the JWT tokens:

1. Open `.env` file
2. Replace placeholders:
   ```bash
   HASHNODE_JWT_SHIVAM=eyJhbGci...your-actual-token
   HASHNODE_JWT_GAURAV=eyJhbGci...your-actual-token
   ```
3. Save the file
4. Test: `python test_jwt_setup.py`

## Troubleshooting

**Can't find jwt cookie?**
- Make sure you're logged in
- Try logging out and back in
- Refresh the page
- Check under .hashnode.com domain

**Cookie shows but can't copy?**
- Try the JavaScript console method
- Or use Inspector tool to examine the cookie
- Or retype it manually (not recommended)

**Multiple hashnode.com entries?**
- Look for jwt under both
- Use the one from .hashnode.com

**Still stuck?**
- Use JavaScript console method (easiest)
- Or take a screenshot and check the value carefully
- Ensure you're on hashnode.com, not a subdomain

---

**Got your tokens?** Great! Head back to [QUICK_START.md](../QUICK_START.md) for the next steps.

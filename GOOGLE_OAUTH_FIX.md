# Google OAuth Configuration Fix

## Problem
The frontend is showing Google OAuth errors because the Google Client ID is not configured for localhost:3000.

## Error Messages
- `[GSI_LOGGER]: The given origin is not allowed for the given client ID`
- `Content-Security-Policy: The page's settings blocked the loading of a resource (connect-src) at https://accounts.google.com/gsi/log`

## Solution

### Step 1: Update Google Cloud Console OAuth Client

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project (or create one if needed)
3. Navigate to **APIs & Services** → **Credentials**
4. Find the OAuth 2.0 Client ID: `1085302344898-g0s003iuj86kdl1acafeqhv5k5r79t36.apps.googleusercontent.com`
5. Click on it to edit the configuration

### Step 2: Configure Authorized JavaScript Origins

Add these origins to **Authorized JavaScript origins**:
```
http://localhost:3000
http://127.0.0.1:3000
https://localhost:3000
https://127.0.0.1:3000
```

### Step 3: Configure Authorized Redirect URIs

Add these URIs to **Authorized redirect URIs**:
```
http://localhost:3000/auth/google/callback
http://127.0.0.1:3000/auth/google/callback
https://localhost:3000/auth/google/callback
https://127.0.0.1:3000/auth/google/callback
```

### Step 4: Save and Test

1. Click **Save** to update the OAuth client
2. Wait a few minutes for changes to propagate
3. Refresh your frontend application
4. Test the Google OAuth login

## Current Configuration

The backend is configured with:
- Client ID: `1085302344898-g0s003iuj86kdl1acafeqhv5k5r79t36.apps.googleusercontent.com`
- Redirect URI: `http://localhost:3000/auth/google/callback`
- Environment: `.env.test`

## CSP Updates

The Content Security Policy has been updated to allow:
- Google OAuth scripts: `https://accounts.google.com/gsi`
- Google OAuth connections: `https://accounts.google.com/gsi`

## Verification

After configuration, you should be able to:
1. Click the Google Sign-In button without errors
2. Complete the OAuth flow successfully
3. See user profile information in the application

## Notes

- Localhost URIs are exempt from HTTPS requirement during development
- Make sure to use HTTP for local development (not HTTPS)
- Changes may take up to 10 minutes to propagate across Google's systems

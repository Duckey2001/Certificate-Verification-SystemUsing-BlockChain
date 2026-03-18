# Google OAuth Setup Guide

## Prerequisites
1. A Google Cloud Platform account
2. Access to Google Cloud Console

## Step 1: Create Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google+ API:
   - Go to "APIs & Services" > "Library"
   - Search for "Google+ API" or "Google Identity Services"
   - Click "Enable"

4. Create OAuth 2.0 Credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - If prompted, configure the OAuth consent screen:
     - Choose "External" (unless you have a Google Workspace)
     - Fill in required fields (App name, User support email, Developer contact)
     - Add scopes: `openid`, `email`, `profile`
     - Add test users if needed
   - Application type: "Web application"
   - Name: "CertiVert"
   - Authorized JavaScript origins:
     - `http://localhost:3000`
     - `http://localhost:8000`
   - Authorized redirect URIs:
     - `http://localhost:3000/auth/google/callback`
   - Click "Create"
   - Copy the **Client ID** and **Client Secret**

## Step 2: Configure Backend

1. Create a `.env` file in the `backend/` directory:
```env
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:3000/auth/google/callback
SECRET_KEY=your-secret-key-for-jwt
DATABASE_URL=sqlite:///./certivert.db
```

## Step 3: Configure Frontend

1. Create a `.env` file in the `frontend/` directory:
```env
REACT_APP_GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
```

2. Restart the React development server after adding the environment variable

## Step 4: Test

1. Start the backend server:
```bash
cd backend
source venv/bin/activate
python3 main.py
```

2. Start the frontend server:
```bash
cd frontend
npm start
```

3. Navigate to `http://localhost:3000/login`
4. Click the "Sign in with Google" button
5. Select your Google account
6. Grant permissions
7. You should be logged in!

## Troubleshooting

### "Google Client ID not configured"
- Make sure you've created a `.env` file in the frontend directory
- Make sure the variable is named `REACT_APP_GOOGLE_CLIENT_ID`
- Restart the React development server after adding the variable

### "Google OAuth not configured"
- Make sure you've created a `.env` file in the backend directory
- Check that `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are set
- Restart the backend server

### "Redirect URI mismatch"
- Make sure the redirect URI in Google Console matches exactly: `http://localhost:3000/auth/google/callback`
- Check that authorized JavaScript origins include `http://localhost:3000`

### "Invalid token audience"
- Make sure the Client ID in frontend `.env` matches the one in backend `.env`
- They should both be the same Google OAuth Client ID

## Production Deployment

For production:
1. Update authorized origins and redirect URIs in Google Console
2. Update environment variables with production URLs
3. Use secure HTTPS URLs
4. Store secrets securely (use environment variables, not hardcoded values)

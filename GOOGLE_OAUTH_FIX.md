# Fixing Google OAuth Authentication

Follow these steps to fix the OAuth authentication issues:

## 1. Update OAuth Client Configuration

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project "nova-calander-integration"
3. Navigate to "APIs & Services" > "Credentials" in the left sidebar
4. Find your OAuth 2.0 Client ID and click the pencil icon to edit it
5. In the "Authorized redirect URIs" section:
   - Add `http://localhost:8080/` (with the trailing slash)
   - Add `http://localhost:8080` (without the trailing slash)
   - Add `urn:ietf:wg:oauth:2.0:oob` (for console-based authentication)
6. Click "Save"

## 2. Update OAuth Consent Screen

1. Navigate to "APIs & Services" > "OAuth consent screen" in the left sidebar
2. Make sure all required fields are filled in:
   - App name: "Nova Assistant"
   - User support email: Your email address
   - Developer contact information: Your email address
3. In the "Test users" section:
   - Make sure your email address is added as a test user
4. Click "Save and Continue" through all steps

## 3. Try Authentication Again

1. Run the simple authentication script:
   ```
   python scripts/simple_google_auth.py
   ```

2. Choose option 2 (Console-based authentication)

3. When the browser opens, you may see a warning about the app not being verified. This is normal for development apps. Click "Continue".

4. After granting permissions, you'll be given a code to copy and paste back into the terminal.

## Troubleshooting

If you still encounter issues:

1. **Check API Enablement**:
   - Make sure the Google Calendar API is enabled for your project
   - Go to "APIs & Services" > "Library" and search for "Google Calendar API"
   - Make sure it shows as "Enabled"

2. **Create New OAuth Credentials**:
   - If all else fails, try creating a new OAuth client ID
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Select "Desktop app" as the application type
   - Name it "Nova Desktop Client"
   - Download the new credentials file and use it in place of the old one

civ# Google Calendar Integration Setup Guide

This guide provides detailed instructions for setting up Google Calendar integration with Nova. By following these steps, you'll enable Nova to access your real calendar events.

## Prerequisites

- A Google account
- Internet connection
- Python 3.6+ with pip installed

## Step 1: Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the project dropdown at the top of the page
3. Click on "New Project"
4. Enter a project name (e.g., "Nova Assistant")
5. Click "Create"
6. Wait for the project to be created and then select it from the dropdown

## Step 2: Enable the Google Calendar API

1. In your new project, navigate to "APIs & Services" > "Library" in the left sidebar
2. Search for "Google Calendar API"
3. Click on "Google Calendar API" in the search results
4. Click the "Enable" button
5. Wait for the API to be enabled

## Step 3: Create OAuth Credentials

1. In the left sidebar, navigate to "APIs & Services" > "Credentials"
2. Click the "Create Credentials" button at the top of the page
3. Select "OAuth client ID" from the dropdown
4. If prompted to configure the OAuth consent screen:
   - Click "Configure Consent Screen"
   - Select "External" user type (unless you have a Google Workspace account)
   - Click "Create"
   - Enter an app name (e.g., "Nova Assistant")
   - Enter your email address for the "User support email" and "Developer contact information" fields
   - Click "Save and Continue"
   - Skip adding scopes by clicking "Save and Continue"
   - Skip adding test users by clicking "Save and Continue"
   - Click "Back to Dashboard"
   - Return to "Credentials" in the left sidebar and click "Create Credentials" > "OAuth client ID" again
5. Select "Desktop app" as the application type
6. Enter a name for the OAuth client (e.g., "Nova Desktop Client")
7. Click "Create"
8. A popup will appear with your client ID and client secret
9. Click "Download JSON" to download the credentials file
10. Save this file somewhere safe (you'll need it in Step 5)

## Step 4: Prepare Your Nova Project

1. Make sure you have installed the required dependencies:
   ```
   pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
   ```
   (These should already be installed if you've updated your requirements.txt)

2. Create a credentials directory in your Nova project (if it doesn't exist):
   ```
   mkdir -p /Users/mouhamed23/nova/credentials
   ```

## Step 5: Set Up Authentication

1. Copy the downloaded OAuth credentials file to your Nova project:
   ```
   cp /path/to/downloaded/credentials.json /Users/mouhamed23/nova/credentials/google_credentials.json
   ```
   Replace `/path/to/downloaded/credentials.json` with the actual path to your downloaded file.

2. Run the setup script to authenticate:
   ```
   python /Users/mouhamed23/nova/scripts/setup_google_calendar.py
   ```

3. A browser window will open asking you to sign in to your Google account
4. Sign in and grant the requested permissions to access your calendar
5. After successful authentication, the browser will display a success message and you can close it
6. The terminal will confirm that authentication was successful

## Step 6: Verify the Integration

1. The setup script will automatically test the connection and show your upcoming events
2. If you want to manually test the integration, you can run:
   ```
   python -c "from core.services.calendar_service import CalendarService; service = CalendarService(); print(service.get_today_schedule())"
   ```

## Troubleshooting

### Authentication Issues

If you encounter authentication errors:
1. Check that your credentials file is correctly placed in `/Users/mouhamed23/nova/credentials/google_credentials.json`
2. Verify that you've enabled the Google Calendar API for your project
3. Try deleting the token file and re-authenticating:
   ```
   rm /Users/mouhamed23/nova/credentials/google_token.pickle
   python /Users/mouhamed23/nova/scripts/setup_google_calendar.py
   ```

### Permission Issues

If Nova can't access your calendar:
1. Make sure you've granted the necessary permissions during the OAuth flow
2. Check that you're using the correct Google account with calendar events
3. Verify that your Google Calendar has events (create a test event if needed)

### API Quota Limits

Google Calendar API has usage limits. If you exceed them:
1. Check the [Google Cloud Console](https://console.cloud.google.com/) for quota information
2. Consider implementing caching to reduce API calls

## Next Steps

After setting up Google Calendar integration:
1. Try asking Nova about your schedule: "What's on my calendar today?"
2. Test different queries like "What meetings do I have tomorrow?" or "Show me my schedule for this week"
3. Nova will now provide real, up-to-date information from your actual calendar

## Additional Resources

- [Google Calendar API Documentation](https://developers.google.com/calendar/api/guides/overview)
- [Google Cloud Console](https://console.cloud.google.com/)
- [OAuth 2.0 for Mobile & Desktop Apps](https://developers.google.com/identity/protocols/oauth2/native-app)

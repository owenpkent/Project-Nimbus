# User Accounts — Setup & Usage Guide

> **Module**: `src/cloud_client.py`  
> **Status**: Implemented — requires Supabase project configuration  
> **Last updated**: March 2026

---

## Overview

Nimbus Adaptive Controller supports optional user accounts for cloud profile sync, premium features, and community features. Accounts are **never required** — all core controller functionality works without signing in.

### What Accounts Enable

| Feature | Free Tier | Nimbus+ ($5–8/mo) |
|---------|-----------|-------------------|
| All layouts, vJoy/ViGEm, profiles | ✅ | ✅ |
| Custom builder, borderless gaming | ✅ | ✅ |
| Game mode, macros | ✅ | ✅ |
| **Cloud profile sync** | — | ✅ |
| **Voice commands** | — | ✅ |
| **AI copilot access** | — | ✅ |
| **Advanced macros** | — | ✅ |

---

## Sign-In Methods

Nimbus supports three sign-in methods:

### 1. Email & Password

Direct email/password authentication through Supabase Auth.

**How to use**:
1. Open **File → Account → Sign In**
2. Enter your email and password
3. Click **"Sign In with Email"**

To create a new account:
1. Click **"Don't have an account? Sign Up"**
2. Enter your email and a password (minimum 6 characters)
3. Click **"Create Account"**
4. Check your email for a confirmation link (if email confirmation is enabled)

### 2. Google OAuth

Sign in with your existing Google account — no new password to remember.

**How to use**:
1. Open **File → Account → Sign In**
2. Click **"Continue with Google"**
3. Your default browser opens to Google's sign-in page
4. Sign in and authorize Nimbus
5. The browser redirects back to the app automatically via `nimbus://auth/callback`

### 3. Facebook OAuth

Sign in with your existing Facebook account.

**How to use**:
1. Open **File → Account → Sign In**
2. Click **"Continue with Facebook"**
3. Your default browser opens to Facebook's sign-in page
4. Sign in and authorize Nimbus
5. The browser redirects back to the app automatically

---

## Authentication Flow (Technical)

```
1. User clicks "Sign In" → AccountDialog.qml opens
2. User chooses method:
   a. Email/password → cloud_client.login_with_email() → Supabase /token endpoint
   b. OAuth (Google/Facebook) → cloud_client.login_with_browser() → system browser
3. On success:
   - Access token + refresh token received
   - Tokens stored in OS credential vault (Windows Credential Manager)
   - User info cached locally for offline display
   - Entitlements checked (free vs Nimbus+)
4. Token auto-refreshes every 50 minutes (tokens expire at 60 min)
5. On app restart, session restored from credential vault
```

### Custom URL Scheme

OAuth callbacks use the `nimbus://` custom URL scheme, registered by the NSIS installer. When the browser redirects to `nimbus://auth/callback?token=...`, Windows routes it back to the running Nimbus app.

**For development** (without installer):
- The URL scheme must be registered manually in the Windows Registry
- Or use email/password login which doesn't require the URL scheme

---

## Token Security

- **No plaintext tokens on disk** — tokens are stored in the Windows Credential Manager via the `keyring` library
- Refresh tokens are rotated on each use
- If the credential vault is unavailable, tokens are held in memory only (lost on app restart)
- All API calls use HTTPS with bearer token authentication

---

## Cloud Profile Sync (Nimbus+ Only)

When signed in with a Nimbus+ subscription, profiles are automatically synced:

- **On save**: Profile JSON is pushed to the cloud
- **On startup**: Remote profiles are pulled and merged with local profiles
- **Merge strategy**: Last-write-wins per profile ID
  - If remote is newer → overwrite local
  - If local is newer → push to remote
  - If profile exists only locally → push to remote
  - If profile exists only remotely → pull to local

### Sync Status

The status ribbon shows sync status when a sync is in progress or completes.

---

## Account Management

### View Account Info
- **File → Account** shows your display name, email, and tier

### Sign Out
- **File → Account → Sign Out** clears all tokens and cached data
- Local profiles are **not** deleted on sign out

### Offline Behaviour
- All local features work without network
- Cloud features degrade gracefully — cached user data displayed
- Profile sync retries on next startup

---

## Backend Setup (For Developers)

The account system uses [Supabase](https://supabase.com) as the backend.

### Required Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `NIMBUS_API_URL` | Supabase project URL | `https://xyz.supabase.co` |
| `NIMBUS_SUPABASE_ANON_KEY` | Supabase anonymous API key | `eyJ...` |
| `NIMBUS_SENTRY_DSN` | Sentry DSN for crash reports | `https://...@sentry.io/...` |
| `NIMBUS_WEB_AUTH_URL` | Web auth page URL | `https://nimbus.app/auth` |

### Supabase Project Setup

1. Create a new Supabase project at [supabase.com](https://supabase.com)
2. Enable **Email/Password** auth in Authentication → Providers
3. Enable **Google** OAuth:
   - Create OAuth credentials in [Google Cloud Console](https://console.cloud.google.com)
   - Add credentials to Supabase → Authentication → Providers → Google
4. Enable **Facebook** OAuth:
   - Create an app in [Facebook Developers](https://developers.facebook.com)
   - Add credentials to Supabase → Authentication → Providers → Facebook
5. Create the required tables:

```sql
-- Profiles table for cloud sync
CREATE TABLE profiles (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    profile_id TEXT NOT NULL,
    data JSONB NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, profile_id)
);

-- Entitlements table for subscription tiers
CREATE TABLE entitlements (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE UNIQUE,
    tier TEXT NOT NULL DEFAULT 'free',
    stripe_customer_id TEXT,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Row Level Security
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE entitlements ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage own profiles"
    ON profiles FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can read own entitlements"
    ON entitlements FOR SELECT USING (auth.uid() = user_id);
```

### Custom URL Scheme Registration (NSIS Installer)

The `nimbus://` URL scheme is registered in `build_tools/installer.nsi`:

```nsi
; Register nimbus:// URL scheme for OAuth callback
WriteRegStr HKCR "nimbus" "" "URL:Nimbus Adaptive Controller"
WriteRegStr HKCR "nimbus" "URL Protocol" ""
WriteRegStr HKCR "nimbus\shell\open\command" "" '"$INSTDIR\${PRODUCT_EXE}" "%1"'
```

---

## Related Files

| File | Purpose |
|------|---------|
| `src/cloud_client.py` | Authentication, sync, and entitlement logic |
| `qml/components/AccountDialog.qml` | Sign-in / account management UI |
| `docs/vision/TELEMETRY_AND_ACCOUNTS.md` | Full architecture proposal |

---

## Troubleshooting

### "Sign in failed" with email/password
- Verify your email and password are correct
- If you haven't confirmed your email, check your inbox for a confirmation link
- Ensure `NIMBUS_API_URL` and `NIMBUS_SUPABASE_ANON_KEY` are configured

### OAuth redirects don't return to the app
- Ensure the `nimbus://` URL scheme is registered (run the installer, or add registry entry manually)
- Check that the Supabase redirect URL is set to `nimbus://auth/callback`

### Tokens not persisting across restarts
- The `keyring` library must be installed: `pip install keyring`
- On Windows, Windows Credential Manager must be accessible
- Run the app as the same user account that stored the tokens

### Profile sync not working
- Confirm you have an active Nimbus+ subscription
- Check network connectivity
- Profiles sync on startup and on save — manual sync via File → Account → Sync Profiles

# Firebase Setup Instructions

## 🔐 Security Warning
**Never commit Firebase service account keys to git!** They contain sensitive credentials.

## Setup Steps

### 1. Get Firebase Service Account Key
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project
3. Go to **Project Settings** > **Service Accounts**
4. Click **Generate New Private Key**
5. Download the JSON file

### 2. Setup for Development
```bash
# Copy your downloaded key to the correct location
cp ~/Downloads/your-firebase-key.json data/serviceAccountKey.json

# Or use the template and fill in your values
cp data/serviceAccountKey.json.template data/serviceAccountKey.json
# Then edit with your actual values
```

### 3. Setup for Production (Docker)

**Option A: Mount as volume**
```bash
docker run -v /path/to/your/serviceAccountKey.json:/app/data/serviceAccountKey.json pixelweather-api
```

**Option B: Environment variable**
```bash
# Set the entire JSON as an environment variable
export GOOGLE_APPLICATION_CREDENTIALS_JSON='{"type":"service_account","project_id":"your-project",...}'
docker run -e GOOGLE_APPLICATION_CREDENTIALS_JSON pixelweather-api
```

## File Structure
```
data/
├── serviceAccountKey.json          # 🚫 NEVER commit this
├── serviceAccountKey.json.template # ✅ Template for reference
```

## Verification
Your Firebase integration should work if:
- The file exists at `data/serviceAccountKey.json`
- The JSON contains valid Firebase credentials
- Firebase project ID matches your app configuration
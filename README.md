# Astroboli - Automated AI Instagram Bot

## Overview
This repository contains two projects:
1.  **iOSGeminiApp**: A manual iOS app to generate and share images.
2.  **Astroboli Bot**: A fully automated Python bot that posts to Instagram daily.

## 🚀 Astroboli Bot Setup (Zero-Input Automation)

To get the daily bot running, you need to configure **GitHub Secrets**.

### Step 1: Get Your API Keys

#### 1. Gemini API Key (`GEMINI_API_KEY`)
*   **Primary Link**: [**Google AI Studio**](https://aistudio.google.com/)
    *   *Instructions*: Sign in, then look for **"Get API key"** in the top-left sidebar.

#### 2. Instagram/Meta Setup (Using your Ads/Business Account)
Since you already have a Meta Ads account, you have a Business Portfolio.

*   **Step A: Create App**: [**Meta Developers - My Apps**](https://developers.facebook.com/apps/)
    *   Click **Create App** > Select **"Business"** (or "Other" > "Business").
    *   **Important**: When asked, select your **existing Business Portfolio** (Ads Account) to link them.
    *   Add **Instagram Graph API** product > "Set Up".
*   **Step B: Get Tokens**: [**Graph API Explorer**](https://developers.facebook.com/tools/explorer/)
    *   Select your new App.
    *   Get User Access Token.
    *   Add Permission: `instagram_content_publish`.



### Step 2: Add Secrets to GitHub
1.  Go to this repository on GitHub.
2.  Click **Settings** > **Secrets and variables** > **Actions**.
3.  Click **New repository secret**.
4.  Add the following three secrets:
    -   `GEMINI_API_KEY`
    -   `IG_ACCESS_TOKEN`
    -   `IG_USER_ID`

### Step 3: Run the Bot
-   The bot is scheduled to run automatically every day at 10:00 UTC.
-   To test it immediately:
    1.  Go to the **Actions** tab.
    2.  Select **Daily Astroboli Post** on the left.
    3.  Click **Run workflow**.

---

## 📱 iOS App Setup (Manual)
1.  Open `iOSGeminiApp.xcodeproj` (or build `project.yml` with `xcodegen`).
2.  Run on iPhone.
3.  Tap "Generate & Post".

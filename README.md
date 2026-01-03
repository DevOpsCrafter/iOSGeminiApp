# Astroboli - Automated AI Instagram Bot

## Overview
This repository contains two projects:
1.  **iOSGeminiApp**: A manual iOS app to generate and share images.
2.  **Astroboli Bot**: A fully automated Python bot that posts to Instagram daily.

## 🚀 Astroboli Bot Setup (Zero-Input Automation)

To get the daily bot running, you need to configure **GitHub Secrets**.

### Step 1: Get Your API Keys
1.  **GEMINI_API_KEY**: Get a free API key from [Google AI Studio](https://makersuite.google.com/app/apikey).
2.  **Instagram Graph API**:
    -   Create a **Meta Developer Account**.
    -   Create a **Facebook App** (Business type).
    -   Add **Instagram Graph API** product.
    -   Link your **Instagram Business Account** to a **Facebook Page**.
    -   Generate a **Long-Lived Access Token**.
    -   **IG_ACCESS_TOKEN**: Your long-lived token.
    -   **IG_USER_ID**: Your Instagram Business Account ID (found via API or Graph Explorer).

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

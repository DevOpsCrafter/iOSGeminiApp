# Astroboli - Automated AI Instagram Bot 🌟

Generate mystical daily Instagram content automatically using AI.

## 🎯 What This Does

Every day at 10:00 UTC (3:30 PM IST), this bot:
1. Generates a unique "Astroboli" themed prompt using **Gemini AI**
2. Creates a stunning 1080x1080 image using **free AI image generation**
3. Writes an engaging caption with 30 hashtags
4. **Emails you** with everything ready to post

You just tap Instagram, select the image, paste the caption, and share. **30 seconds total.** ✨

---

## 🚀 Quick Setup (10 Minutes)

### Step 1: Get Your API Keys

#### 1. Gemini API Key
*   Visit [**Google AI Studio**](https://aistudio.google.com/)
*   Sign in → Click **"Get API key"** in sidebar
*   Copy the key (starts with `AIza...`)

#### 2. Gmail App Password
Since Meta Developer access has restrictions, we use email delivery instead.

**Create App Password:**
1. **Enable 2FA** (if not done): [Google Account Security](https://myaccount.google.com/security)
2. **Generate Password**: [App Passwords](https://myaccount.google.com/apppasswords)
3. Select **Mail** → Click **Generate**
4. **Copy the 16-character password** (e.g., `xxxx xxxx xxxx xxxx`)

---

### Step 2: Configure Credentials

1. **Rename** `secrets.env.template` to `secrets.env`
2. **Edit** `secrets.env` with your keys:
   ```env
   GEMINI_API_KEY=AIzaSy...
   YOUR_EMAIL=your.email@gmail.com
   EMAIL_PASSWORD=xxxx xxxx xxxx xxxx
   ```
3. **Upload to GitHub**:
   ```powershell
   ./sync_secrets.ps1
   ```

---

### Step 3: Test It!

**Manual Trigger:**
1. Go to GitHub → **Actions** tab
2. Select **"Daily Astroboli Post"**
3. Click **"Run workflow"**
4. Wait 1 minute
5. **Check your email!** 📧

---

## 📋 What You Get in the Email

- 🖼️ **High-quality image** (1080x1080, ready for Instagram)
- 📝 **Engaging caption** with mystical astrology theme
- #️⃣ **30 relevant hashtags**
- 📱 **Simple posting instructions**

---

## ⚙️ How It Works

```
┌─────────────────────────────────┐
│  GitHub Actions (Daily 10 AM)  │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  Gemini AI generates content    │
│  Model: gemini-2.5-flash (FREE) │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  Pollinations.ai creates image  │
│  (FREE, unlimited)              │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  Email sent with attachment     │
│  via Gmail SMTP                 │
└─────────────────────────────────┘
```

---

## 💰 Cost Breakdown

| Service | Price | Our Usage |
|---------|-------|-----------|
| **Gemini 2.5 Flash** | FREE (1,500/day limit) | 1/day |
| **Pollinations.ai** | FREE (unlimited) | 1/day |
| **GitHub Actions** | FREE (2,000 min/month) | ~60 min/month |
| **Total** | **$0.00/month** | ✅ |

---

## 🛠️ Troubleshooting

### Email Not Received?
- Check spam folder
- Verify Gmail App Password is correct
- Ensure 2FA is enabled on Google account

### Workflow Failed?
- Check GitHub Actions logs
- Verify all 3 secrets are set in GitHub → Settings → Secrets

### Want to Change Schedule?
Edit `.github/workflows/daily_post.yml`:
```yaml
schedule:
  - cron: '0 10 * * *'  # Change time here (UTC)
```

---

## 📊 Why Email Instead of Direct Posting?

**Email Solution:**
- ✅ Works immediately (no Meta approval)
- ✅ 100% free forever
- ✅ No token expiry or maintenance
- ✅ Full content control before posting
- ❌ Requires 30 seconds manual posting

**Instagram Graph API:**
- ✅ Fully automated (zero-click)
- ❌ Requires Meta Developer approval (weeks)
- ❌ Business account mandatory
- ❌ OAuth token expires every 60 days
- ❌ Complex setup (10+ steps)
- ❌ User's Meta account lacks access (current blocker)

**For single-user daily posting, email is superior.** 🎯

---

## 🎨 Customization

### Change the Theme
Edit `daily_bot.py` line 27-37 to modify the prompt

### Add More Hashtags
Edit the caption generation logic in `daily_bot.py`

### Multiple Posts Per Day
Duplicate the cron schedule in `daily_post.yml`

---

## 📁 Project Structure

```
iOSGeminiApp/
├── daily_bot.py              # Main bot script
├── requirements.txt           # Python dependencies
├── secrets.env               # Your API keys (local, gitignored)
├── secrets.env.template      # Template for setup
├── sync_secrets.ps1          # Upload secrets to GitHub
├── .github/workflows/
│   └── daily_post.yml        # GitHub Actions schedule
└── README.md                 # This file
```

---

## 🤝 Support

Issues? Questions? Open a GitHub issue or check the [implementation plan](C:\Users\Pushkar\.gemini\antigravity\brain\02309b20-978f-4bec-bfa9-38c443e1d0e8\implementation_plan.md) for detailed technical docs.

---

**Built with ❤️ using Gemini AI, Pollinations.ai, and GitHub Actions**
: A fully automated Python bot that posts to Instagram daily.

## 🚀 Astroboli Bot Setup (Zero-Input Automation)

To get the daily bot running, you need to configure **GitHub Secrets**.


#### 1. Gemini API Key (`GEMINI_API_KEY`)
*   **Primary Link**: [**Google AI Studio**](https://aistudio.google.com/)
    *   *Instructions*: Sign in, then look for **"Get API key"** in the top-left sidebar.

#### 2. Email Setup (Gmail App Password)

Since Meta Developer access has restrictions, we're using **email delivery** instead. The bot will email you the generated image daily.

**Step A: Enable 2-Factor Authentication** (IF NOT ALREADY DONE)
1. Go to [**Google Account Security**](https://myaccount.google.com/security)
2. Click **2-Step Verification** → **Get Started**
3. Follow the prompts to set it up

**Step B: Create App Password**
1. Go to [**App Passwords**](https://myaccount.google.com/apppasswords)
2. In the dropdown, select **Mail** (or type "Astroboli Bot")
3. Click **Generate**
4. **Copy the 16-character password** (format: `xxxx xxxx xxxx xxxx`)
5. Save this - it's your `EMAIL_PASSWORD`

**What you'll need:**
- `YOUR_EMAIL`: Your Gmail address (e.g., `yourname@gmail.com`)
- `EMAIL_PASSWORD`: The 16-character app password you just created
### Step 2: Configure Your Credentials
1.  Go to this repository on GitHub.
2.  Click **Settings** > **Secrets and variables** > **Actions**.
3.  Click **New repository secret**.
4.  Add the following three secrets:
    -   `GEMINI_API_KEY`
    -   `YOUR_EMAIL`
    -   `EMAIL_PASSWORD`

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

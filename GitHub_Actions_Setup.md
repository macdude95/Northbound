# GitHub Actions Automation Setup Guide

This guide shows how to set up automated daily strategy notifications using GitHub Actions (completely free).

## 🚀 Quick Setup (5 minutes)

### Step 1: Push Code to GitHub

```bash
# Add the workflow file
git add .github/workflows/daily-strategy.yml
git add GitHub_Actions_Setup.md

# Commit and push
git commit -m "Add GitHub Actions automation"
git push origin main
```

### Step 2: Configure Notification Secrets

1. **Go to your GitHub repository**
2. **Click "Settings" tab**
3. **Click "Secrets and variables" → "Actions"**
4. **Click "New repository secret"** (do this twice)

**Add these two secrets:**

**Secret 1 - Polygon API Key:**

- **Name:** `POLYGON_API_KEY`
- **Value:** Your Polygon.io API key (get from https://polygon.io/)

**Secret 2 - Email:**

- **Name:** `EMAIL_ADDRESS`
- **Value:** Your email address (e.g., `yourname@gmail.com`)

## 🧪 Test the Setup

### Manual Test Run:

1. **Go to GitHub repository**
2. **Click "Actions" tab**
3. **Click "Daily Strategy Alert"**
4. **Click "Run workflow" button**
5. **Check your email** for the strategy notification

### Local Testing:

You can also test the script locally:

```bash
# Interactive mode (with portfolio input)
python daily_strategy.py

# Automated mode (skip portfolio input)
python daily_strategy.py --skip-portfolio
```

### Check Logs:

- **Click on the workflow run**
- **Scroll down to see script output**
- **Verify allocation extraction worked**

## ⏰ Schedule Details

- **Runs:** Monday-Friday at 8 AM Eastern Time
- **Timezone:** Automatically adjusts for daylight saving
- **Manual trigger:** "Run workflow" button for testing

## 📧 Notification Format

You'll receive **email notifications** with the strategy results:

```
Daily Strategy - 2025-12-28
Target Allocation: TQQQ: 64.7% SQQQ: 35.3%

Full Output:
[Complete strategy analysis]
```

## 🛠️ Troubleshooting

### No Email Received:

1. **Check spam/junk folder** (automated emails often go there)
2. **Verify EMAIL_ADDRESS secret** is correct
3. **Test with manual workflow run**
4. **Check Actions logs** for email sending errors

### Script Errors:

- **Check "Actions" tab** for error logs
- **Verify all dependencies** are in `requirements.txt`
- **Test locally** with `python daily_strategy.py --skip-portfolio`

### Mail Command Issues:

- **GitHub Actions automatically installs mailutils** for email functionality
- **If mail still fails**, check that EMAIL_ADDRESS secret is properly set

### Timezone Issues:

- **Workflow runs in UTC** (8 AM ET = 12:00 UTC)
- **Adjust cron schedule** if needed: `0 12 * * 1-5`

## 🎯 Advanced Configuration

### Change Run Time:

Edit the cron schedule in `.github/workflows/daily-strategy.yml`:

```yaml
# 9 AM ET = 13:00 UTC
- cron: '0 13 * * 1-5'
```

### Add More Notifications:

```yaml
# Send to multiple email addresses
echo "$BODY" | mail -s "$SUBJECT" email1@example.com email2@example.com
```

### Custom Logic:

Modify the notification step to add custom filtering or alerts.

## 💰 Cost Summary

- **GitHub Actions:** Free (2,000 minutes/month)
- **Email notifications:** Free
- **Total:** $0/month

## ✅ Success Checklist

- [ ] Code pushed to GitHub
- [ ] POLYGON_API_KEY and EMAIL_ADDRESS secrets configured
- [ ] Manual test run successful
- [ ] Email notifications received

Once set up, you'll get automated daily notifications every weekday morning!

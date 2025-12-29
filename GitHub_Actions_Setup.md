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

**Secret 1 - SMS:**

- **Name:** `PHONE_NUMBER`
- **Value:** Your phone number + carrier gateway (e.g., `1234567890@tmomail.net`)

**Secret 2 - Email:**

- **Name:** `EMAIL_ADDRESS`
- **Value:** Your email address (e.g., `yourname@gmail.com`)

**SMS Carrier Examples:**

- **AT&T:** `1234567890@txt.att.net`
- **Verizon:** `1234567890@vtext.com`
- **T-Mobile:** `1234567890@tmomail.net`
- **Sprint:** `1234567890@messaging.sprintpcs.com`

## 🧪 Test the Setup

### Manual Test Run:

1. **Go to GitHub repository**
2. **Click "Actions" tab**
3. **Click "Daily Strategy Alert"**
4. **Click "Run workflow" button**
5. **Check your phone for SMS notification**

### Check Logs:

- **Click on the workflow run**
- **Scroll down to see script output**
- **Verify allocation extraction worked**

## ⏰ Schedule Details

- **Runs:** Monday-Friday at 8 AM Eastern Time
- **Timezone:** Automatically adjusts for daylight saving
- **Manual trigger:** "Run workflow" button for testing

## 📱 Notification Format

You'll receive **both SMS and email** notifications with the same content:

```
Daily Strategy - 2025-12-28
Target Allocation: TQQQ: 64.7% SQQQ: 35.3%

Full Output:
[Complete strategy analysis]
```

## 🛠️ Troubleshooting

### No SMS Received:

1. **Verify phone number/carrier** in workflow file
2. **Check spam folder** (sometimes goes there)
3. **Test with manual workflow run**
4. **Check Actions logs** for email sending errors

### Script Errors:

- **Check "Actions" tab** for error logs
- **Verify all dependencies** are in `requirements.txt`
- **Test locally** with `python daily_strategy.py`

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
# Send to multiple numbers
echo "$BODY" | mail -s "$SUBJECT" phone1@carrier.com phone2@carrier.com
```

### Custom Logic:

Modify the notification step to add custom filtering or alerts.

## 💰 Cost Summary

- **GitHub Actions:** Free (2,000 minutes/month)
- **SMS:** Free (email-to-SMS gateway)
- **Total:** $0/month

## ✅ Success Checklist

- [ ] Code pushed to GitHub
- [ ] PHONE_NUMBER and EMAIL_ADDRESS secrets configured
- [ ] Manual test run successful
- [ ] SMS and email notifications received

Once set up, you'll get automated daily notifications every weekday morning!

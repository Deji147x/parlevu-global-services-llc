# Buffer.com Social Media Automation Setup

## Step 1: Get Your Buffer Profile IDs

1. **Log into Buffer.com** (buffer.com)
2. Go to **Settings → Connected Apps**
3. Look for your connected social media profiles (Facebook, Instagram, LinkedIn, X, Pinterest)
4. Find the **Profile ID** for each platform you want to post to
   - May be visible in Settings or Profile details
   - Or use Buffer API: https://api.bufferapp.com/1/user.json?access_token=YOUR_KEY

Example output from Buffer API:
```json
{
  "success": true,
  "profiles": [
    {
      "id": "5e1b2c3d4e5f6g7h8i9j0k1l",
      "service": "facebook",
      "formatted_service": "Facebook"
    },
    {
      "id": "5a1b2c3d4e5f6g7h8i9j0k2l",
      "service": "twitter",
      "formatted_service": "X"
    }
  ]
}
```

## Step 2: Update .env File

Edit `.env` in the repo root:

```
BUFFER_API_KEY=u8F9bepCRT_69QaJInUOSzvA2oMQDkvQWw7JxPLZS8_
BUFFER_PROFILE_ID=5e1b2c3d4e5f6g7h8i9j0k1l
SITE_URL=https://www.parlevugloballlc.com
```

**For multiple profiles**, create a script that posts to each:

```python
# Post to Facebook, then LinkedIn, then X
for profile_id in ["5e1b2c3d...", "5a1b2c3d...", "5f1b2c3d..."]:
    post_to_buffer(post, profile_id)
```

## Step 3: Set Up Cron Job (Linux/Mac)

Add to crontab (`crontab -e`):

```bash
# Post to Buffer every Monday, Wednesday, Friday at 9 AM
0 9 * * 1,3,5 cd /path/to/repo && python3 tools/post_to_buffer.py --posts 3

# Or post every day (1 post per day)
0 9 * * * cd /path/to/repo && python3 tools/post_to_buffer.py --posts 1
```

## Step 4: Set Up Cron Job (Windows)

Use **Task Scheduler**:

1. Open **Task Scheduler**
2. Click **Create Basic Task**
   - Name: "Post to Buffer - Parlevu"
   - Trigger: Repeating (Monday, Wednesday, Friday at 9:00 AM)
   - Action: Start a program
   - Program: `C:\Python\python3.exe`
   - Arguments: `C:\path\to\repo\tools\post_to_buffer.py --posts 3`
   - Start in: `C:\path\to\repo\`

## Step 5: Test the Script

Run manually first:

```bash
# Dry run (shows what would post)
python3 tools/post_to_buffer.py --posts 3 --dry-run

# Post immediately (for testing)
python3 tools/post_to_buffer.py --posts 1 --now

# Schedule for next Mon/Wed/Fri (production)
python3 tools/post_to_buffer.py --posts 3
```

## What Gets Posted

Each post includes:
- **Title** of the blog post
- **First sentence** of the article
- **Call-to-action:** "Learn more about selling your [state] home for cash"
- **Hashtags:** #CashBuyer #RealEstate #[State]
- **Link** to the full blog post on parlevugloballlc.com

Example:
```
✨ We Buy Houses Baltimore Fast — No Realtor, No Wait, No Repairs

Your Baltimore home can close in a week. No agent. No repairs.

Learn more about selling your Baltimore home for cash. No repairs. No fees. No agent commissions.

#CashBuyer #RealEstate #Maryland
```

## Troubleshooting

**"ERROR: BUFFER_API_KEY not set"**
- Make sure `.env` file exists in the repo root
- Check that BUFFER_API_KEY line is present

**"ERROR: BUFFER_PROFILE_ID not set"**
- Get your profile ID from Buffer.com settings
- Add it to `.env` file as `BUFFER_PROFILE_ID=`

**Posts not appearing in Buffer**
- Check Buffer.com directly (may be in queue)
- Verify profile ID is correct
- Try `--now` flag for immediate posting
- Check Buffer dashboard for errors

**"charmap codec" errors**
- Update `.env` to use UTF-8 encoding
- Or run on Linux/Mac (better Unicode support)

## API Key Security

⚠️ **NEVER commit `.env` to git**

- `.env` is in `.gitignore` (won't be committed)
- Keep API key secret and rotate quarterly
- If exposed, revoke key in Buffer.com settings and generate a new one

## Next Steps

1. ✅ Get Buffer profile IDs for each social platform
2. ✅ Update `.env` with profile IDs
3. ✅ Test with `python3 tools/post_to_buffer.py --posts 1 --now`
4. ✅ Set up cron job (Linux/Mac) or Task Scheduler (Windows)
5. ✅ Posts will auto-share 3x/week (Mon/Wed/Fri at 9 AM)

---

**Questions?** Check Buffer API docs: https://buffer.com/developers/api

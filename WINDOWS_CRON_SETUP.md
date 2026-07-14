# Windows Task Scheduler Setup for Buffer Posting

## Overview
This guide sets up automatic posting to Buffer.com 3x per week (Monday, Wednesday, Friday at 9 AM) using Windows Task Scheduler.

## Prerequisites
- Python 3 installed and available in PATH
- `.env` file configured with valid BUFFER_API_KEY and BUFFER_PROFILE_ID
- Repository path: `C:\Users\Parlevu_Global\parlevu-global-services-llc`

## Setup Instructions

### Step 1: Open Task Scheduler

1. Press **Windows + R**
2. Type `taskschd.msc` and press Enter
3. Click **Create Basic Task** (right panel)

### Step 2: Configure Task Name & Description

- **Name:** `Parlevu Buffer Posts - 3x Weekly`
- **Description:** Post latest Parlevu blog posts to Buffer (Mon/Wed/Fri 9 AM)
- Click **Next**

### Step 3: Set Trigger (Schedule)

1. Select **Weekly**
2. Click **Next**
3. Configure:
   - **Start:** Today's date
   - **Recur every:** 1 week
   - **Check boxes:** Monday, Wednesday, Friday only
   - **Start time:** 09:00 AM
   - **Repeat task every:** Leave unchecked (runs once per day)

Click **Next**

### Step 4: Set Action

1. Select **Start a program**
2. Click **Next**
3. Configure:
   - **Program/script:** `C:\Users\Parlevu_Global\AppData\Local\Programs\Python\Python311\python.exe`
     (Or find your Python path: run `python -c "import sys; print(sys.executable)"`)
   - **Add arguments:** `tools/post_to_buffer.py --posts 3`
   - **Start in:** `C:\Users\Parlevu_Global\parlevu-global-services-llc`

Click **Next**

### Step 5: Finish

Review settings and click **Finish**

## Verify Setup

### Method 1: Check Task Scheduler
1. In Task Scheduler, find **"Parlevu Buffer Posts - 3x Weekly"**
2. Right-click → **Run** to test immediately
3. Check **Last Run Result** (should show success after running)

### Method 2: Test Manually
```powershell
cd C:\Users\Parlevu_Global\parlevu-global-services-llc
python tools/post_to_buffer.py --posts 1 --now --dry-run
```

Output should show the posts that would be shared.

### Method 3: Check Logs
After running, check:
- Windows Event Viewer → Windows Logs → System (search for "Parlevu")
- Or redirect output to a log file (see Advanced section below)

## Advanced Setup: Log File Output

To capture script output in a log file:

### Step 1: Create Batch Wrapper Script

Create file: `C:\Users\Parlevu_Global\parlevu-global-services-llc\post_to_buffer.bat`

```batch
@echo off
cd /d "C:\Users\Parlevu_Global\parlevu-global-services-llc"
python tools/post_to_buffer.py --posts 3 >> logs/buffer_posts.log 2>&1
```

### Step 2: Create Logs Directory
```powershell
mkdir C:\Users\Parlevu_Global\parlevu-global-services-llc\logs
```

### Step 3: Update Task Scheduler

In the **Action** step, set:
- **Program/script:** `C:\Users\Parlevu_Global\parlevu-global-services-llc\post_to_buffer.bat`
- **Start in:** `C:\Users\Parlevu_Global\parlevu-global-services-llc`

Now all output is saved to `logs/buffer_posts.log`

## Troubleshooting

### Task runs but nothing posts
- Check `.env` file exists in repo root
- Verify BUFFER_API_KEY is valid: `curl "https://api.bufferapp.com/1/user.json?access_token=YOUR_KEY"`
- Check logs: `type logs/buffer_posts.log`

### "Python not found" error
- Find your Python path: `python -c "import sys; print(sys.executable)"`
- Update the full path in Task Scheduler

### Task won't run at all
- Right-click task → **Properties** → **Run whether user is logged in or not**
- Make sure user account has permission to run scripts

### Posts not appearing in Buffer
- Check Buffer.com directly (posts may be scheduled for future)
- Verify BUFFER_PROFILE_ID is correct in `.env`
- Try `--now` flag: `python tools/post_to_buffer.py --posts 1 --now`

## Testing Commands

```powershell
# Dry run (shows what would be posted)
python tools/post_to_buffer.py --posts 3 --dry-run

# Post immediately (for testing)
python tools/post_to_buffer.py --posts 1 --now

# Schedule for Mon/Wed/Fri 9 AM (production)
python tools/post_to_buffer.py --posts 3

# Check environment variables
python -c "import os; print('BUFFER_API_KEY:', os.getenv('BUFFER_API_KEY', 'NOT SET'))"
```

## Next Steps

1. ✅ Set up Task Scheduler (this guide)
2. ✅ Test with `--dry-run` flag
3. ✅ Verify Buffer API key is valid
4. ✅ Get Buffer profile IDs for each social platform
5. ✅ Update `.env` with profile IDs
6. ✅ Enable automatic posting (Mon/Wed/Fri 9 AM)

## Automatic Posting Schedule

Once configured, your Parlevu blog posts will automatically post to Buffer:
- **Monday 9 AM:** 1 post
- **Wednesday 9 AM:** 1 post  
- **Friday 9 AM:** 1 post

Total: **3 posts/week** from your 91-post blog library

Posts are randomly selected from the newest published content, with captions tailored to each social platform.

---

Questions? Check: BUFFER_DEPLOYMENT.md (API setup) or tools/post_to_buffer.py (script details)

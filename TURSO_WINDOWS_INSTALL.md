# 🪟 Installing Turso CLI on Windows

**Quick guide to get Turso CLI working on your Windows system**

---

## Method 1: PowerShell Installation (Recommended)

This is the **easiest and fastest** method.

### Step 1: Open PowerShell as Administrator

1. Press `Windows Key`
2. Type `PowerShell`
3. Right-click on "Windows PowerShell"
4. Click **"Run as Administrator"**
5. Click "Yes" on the security prompt

### Step 2: Run the Installation Command

Copy and paste this command into PowerShell:

```powershell
powershell -c "irm https://raw.githubusercontent.com/tursodatabase/turso-cli/main/install.ps1 | iex"
```

Press `Enter` and wait for installation to complete.

**Expected output:**
```
Downloading Turso CLI...
Installing to C:\Users\YourName\.turso\bin\turso.exe
Adding to PATH...
Installation complete!
```

### Step 3: Restart Git Bash

1. **Close** your current Git Bash window
2. **Open** a new Git Bash window
3. Test the installation:

```bash
turso --version
```

**Expected output:**
```
turso version v0.x.x
```

✅ **Success!** Turso CLI is installed.

---

## Method 2: Manual Download (If PowerShell Fails)

If the PowerShell script doesn't work, download manually:

### Step 1: Download the Windows Binary

1. Go to: **https://github.com/tursodatabase/turso-cli/releases/latest**
2. Scroll down to **"Assets"**
3. Download: **`turso-windows-amd64.exe`** or **`turso_windows_x64.zip`**

### Step 2: Extract and Install

**If you downloaded `.exe`:**
1. Rename `turso-windows-amd64.exe` to `turso.exe`
2. Move to: `C:\Program Files\Turso\` (create folder if needed)

**If you downloaded `.zip`:**
1. Extract the zip file
2. Find `turso.exe` inside
3. Move to: `C:\Program Files\Turso\`

### Step 3: Add to PATH

**Option A - Quick (Git Bash only):**

Add this line to your `~/.bashrc`:

```bash
echo 'export PATH="/c/Program Files/Turso:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

**Option B - Permanent (All terminals):**

1. Press `Windows Key`
2. Search for "Environment Variables"
3. Click "Edit the system environment variables"
4. Click "Environment Variables..." button
5. Under "System variables", find "Path"
6. Click "Edit"
7. Click "New"
8. Add: `C:\Program Files\Turso`
9. Click "OK" on all windows
10. **Restart Git Bash**

### Step 4: Test Installation

```bash
turso --version
```

✅ **Success!** Turso CLI is installed.

---

## Troubleshooting

### Problem: "command not found" after installation

**Solution:**
```bash
# Check if turso.exe exists
ls "/c/Program Files/Turso/turso.exe"

# If exists, add to PATH manually:
export PATH="/c/Program Files/Turso:$PATH"

# Make it permanent:
echo 'export PATH="/c/Program Files/Turso:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Problem: PowerShell script blocked

**Solution:**
1. Open PowerShell as Administrator
2. Run: `Set-ExecutionPolicy RemoteSigned`
3. Type `Y` and press Enter
4. Try installation again
5. After installation: `Set-ExecutionPolicy Restricted` (restore security)

### Problem: SSL/TLS errors during download

**Solution:**
```powershell
# In PowerShell
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
# Then retry installation command
```

### Problem: "Access Denied" or permission errors

**Solution:**
- Make sure you're running PowerShell **as Administrator**
- Or install to user directory instead:
  ```bash
  mkdir -p ~/bin
  # Download turso.exe to ~/bin/
  export PATH="$HOME/bin:$PATH"
  echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
  ```

---

## Next Steps

Once Turso CLI is installed successfully:

1. **Sign up for Turso:**
   ```bash
   turso auth signup
   ```

2. **Login:**
   ```bash
   turso auth login
   ```

3. **Create your database:**
   ```bash
   turso db create alberta-construction
   ```

4. **Continue with deployment:**
   See [DEPLOYMENT.md](DEPLOYMENT.md) for full deployment guide.

---

## Quick Test

Run these commands to verify everything works:

```bash
# Check version
turso --version

# Check if you're logged in
turso auth whoami

# If not logged in, do this:
turso auth login
```

---

## Alternative: Use Turso Web Dashboard

If CLI installation continues to fail, you can use Turso's web dashboard:

1. Go to: **https://turso.tech/**
2. Sign up for free account
3. Use the web UI to create database
4. Upload database via web interface (if available)
5. Get credentials from dashboard
6. Skip CLI steps in DEPLOYMENT.md

**Note:** The CLI is more convenient, but the web dashboard works too!

---

**Need more help?**
- Turso Discord: https://discord.gg/turso
- Turso Docs: https://docs.turso.tech/cli/installation
- GitHub Issues: https://github.com/tursodatabase/turso-cli/issues

---

**Last Updated:** December 10, 2025

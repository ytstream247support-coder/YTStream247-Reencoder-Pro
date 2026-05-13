# Complete macOS Build Guide (Zero Mac Experience Required)

## What You Get at the End

A file called `YT-FFmpeg-Stream-Reencoder-macOS.dmg` — a single disk image that works on **both Intel Macs and Apple Silicon (M1/M2/M3/M4)**. Users drag the app to Applications and run it.

---

## Step 1 — Rent a Mac (Cheapest/Fastest Options)

You need a **real macOS machine** — PyInstaller can't build Mac apps from Windows. Choose one:

### Option A — MacinCloud (easiest, ~$1/hr, fastest to start)
1. Go to https://www.macincloud.com
2. Choose **Pay-as-you-go Server** — M-series available
3. Sign up, pay $1 for first hour (~$30 for a full day)
4. You'll connect via **Microsoft Remote Desktop** (download free from Microsoft Store on your PC)
5. You get a full macOS desktop in a window on your PC

### Option B — Scaleway Mac mini M2 Pro (~€0.11/hr hourly billing)
1. https://www.scaleway.com/en/elastic-metal/mac-mini/
2. Requires EU billing/address
3. 24-hour minimum first boot, then hourly

### Option C — AWS EC2 mac2.metal (M1, ~$0.65/hr, 24hr minimum)
Professional but more complex setup.

**Recommendation for urgent release:** MacinCloud — you can be building in 15 minutes.

---

## Step 2 — Prepare Files on Your Windows PC (Before Renting)

Before you start the Mac clock, zip your project so upload is quick:

1. You must have the **4 FFmpeg zip files** for Mac. Check the folder `mac-ffmpeg/`:
   - `ffmpeg-mac-arm64.zip`
   - `ffprobe-mac-arm64.zip`
   - `ffmpeg-mac-intel.zip`
   - `ffprobe-mac-intel.zip`

   If you don't have them, download from https://evermeet.cx/ffmpeg/ (arm64 + intel versions of both ffmpeg and ffprobe), and name the zips exactly as above. Each zip should contain exactly one binary named `ffmpeg` or `ffprobe`.

2. Upload your entire project folder to Mac via:
   - **Google Drive** / **Dropbox** (drop folder, download on Mac) — easiest
   - Or **GitHub** if it's already pushed

---

## Step 3 — First Time on the Rented Mac

Once you have a macOS desktop open (via Remote Desktop or browser):

### 3.1 Open Terminal
Press `Cmd + Space` → type `Terminal` → Enter. You'll use this for everything.

### 3.2 Install Xcode Command Line Tools (~5 min, one-time)
```bash
xcode-select --install
```
A dialog appears → click **Install** → wait. This gives you `git`, compilers, `codesign`, etc.

### 3.3 Install Python 3
Check if Python is already there:
```bash
python3 --version
```
If not (or below 3.8), install from https://www.python.org/downloads/macos/ — download the **universal2 installer** and run it.

### 3.4 Get the Project on the Mac
From your Google Drive download, or:
```bash
cd ~/Desktop
git clone <your-repo-url>
cd "YT FFmpeg Stream Reencoder"
```

### 3.5 Install Python Dependencies
```bash
pip3 install -r requirements.txt
pip3 install pyinstaller
```

---

## Step 4 — Icons (Automatic!)

`installer/macos/build_dmg.sh` automatically generates the macOS icon (`.icns`) from your existing `assets/icons/icon.png`. You don't need to do anything — the build script detects the PNG and uses `sips` + `iconutil` (both built into macOS) to create all 10 required sizes (16×16 up to 1024×1024) and bundle it into the app.

As long as `assets/icons/icon.png` exists in your project, **your app icon will show correctly** in Finder, Dock, and Launchpad.

**Tip:** For best quality, `assets/icons/icon.png` should be **1024×1024 pixels** (or at least 512×512). Lower resolutions get blurry when scaled up.

---

## Step 5 — Build the DMG (One Command!)

From the project root on the Mac:
```bash
python3 build.py
```

This runs automatically:
1. PyInstaller builds a **universal2** app (works on Intel + ARM)
2. Creates `.app` bundle structure
3. Generates `icon.icns` from your PNG
4. Creates `Info.plist` with app metadata
5. Bundles all 4 FFmpeg binaries
6. Verifies each binary's architecture
7. Applies **ad-hoc code signature** (reduces Gatekeeper warnings even without a paid Apple cert)
8. Copies `FIRST-RUN (read me).txt` into the DMG
9. Packages into `YT-FFmpeg-Stream-Reencoder-macOS.dmg`

**Takes:** ~3–10 minutes depending on Mac.

**Output file:** `YT-FFmpeg-Stream-Reencoder-macOS.dmg` in the project root.

---

## Step 6 — Test the DMG on the Same Mac

1. Double-click the `.dmg` → Finder window opens showing the app + Applications shortcut + read-me file
2. Drag app icon → Applications folder
3. Open Applications, **right-click the app → Open** (important first time!) → click **Open** in the prompt
4. App should launch. Do a test re-encode to verify FFmpeg works.

---

## Step 7 — Download the DMG Back to Your PC

From the Mac Terminal:
```bash
cp YT-FFmpeg-Stream-Reencoder-macOS.dmg ~/Desktop/
```
Then use the Remote Desktop file-transfer feature, or upload it to Google Drive from the Mac and download on your PC.

---

## Step 8 — What Users See & Do

Because you don't have a **paid Apple Developer ID** ($99/yr) and **notarization**, macOS will warn users on first launch. The DMG now includes a `FIRST-RUN (read me).txt` file with instructions, but also include these steps in your release notes:

### For users — First-time opening on macOS:

> 1. Double-click the downloaded `.dmg` file
> 2. Drag **YT Stream 24/7 - Reencoder** to the **Applications** folder
> 3. Open **Applications**, **right-click** the app, and choose **Open**
> 4. Click **Open** in the security dialog
>
> A normal double-click won't work the first time — you must use right-click → Open.
>
> If macOS still blocks: **System Settings → Privacy & Security** → scroll to the blocked-app message → click **Open Anyway**.
>
> After the first successful launch, the app opens normally forever.

---

## Quick Reference Card

| What | Command | Where |
|------|---------|-------|
| Install dev tools | `xcode-select --install` | Mac Terminal |
| Install deps | `pip3 install -r requirements.txt pyinstaller` | Mac, project root |
| Build everything | `python3 build.py` | Mac, project root |
| Output file | `YT-FFmpeg-Stream-Reencoder-macOS.dmg` | Project root |

---

## Time & Cost Estimate

| Step | Time | Cost |
|------|------|------|
| Sign up MacinCloud + connect | 15 min | $1 |
| Install Xcode CLT + Python | 15 min | — |
| Upload project + install deps | 10 min | — |
| Build + test DMG | 15 min | — |
| Download DMG, disconnect | 5 min | — |
| **Total** | **~1 hour** | **~$2–5** |

You don't need to rent a full day — one hour of MacinCloud pay-as-you-go gets you a working DMG.

---

## Likely Problems & Fixes

| Problem | Fix |
|---------|-----|
| `pyinstaller: command not found` | `pip3 install pyinstaller` then restart terminal |
| `Could not find macOS FFmpeg inputs` | Make sure the 4 zips are in `mac-ffmpeg/` folder |
| `sips: command not found` | You're not on macOS — this won't happen on Mac |
| `universal2 failure` | Use the official Python.org universal2 installer, not Homebrew Python |
| App won't open on tester's Mac | Tell them right-click → Open (don't double-click the first time) |
| Icon not showing | Ensure `assets/icons/icon.png` exists and is ≥512×512 |

---

## Build Script Features (What's Already Automated)

The `installer/macos/build_dmg.sh` script handles:

- **Icon generation:** `generate_icns_from_png()` auto-converts `assets/icons/icon.png` to proper macOS ICNS with all 10 required sizes
- **Ad-hoc codesigning:** `codesign --force --deep --sign -` applied to all 4 FFmpeg binaries and the app bundle — significantly reduces Gatekeeper warnings even without a paid Apple cert
- **Architecture verification:** Checks each FFmpeg binary is the correct arm64/x86_64 via the `file` command
- **Info.plist generation:** Creates correct bundle metadata (identifier, version, icon reference)
- **DMG read-me:** Copies `FIRST-RUN (read me).txt` into the disk image

All of this runs automatically from `python3 build.py` — no manual steps needed.

---

## Optional: Future Production Release (Signed + Notarized)

When you're ready for a proper signed release (removes all warnings):

1. Buy Apple Developer Program membership ($99/year) at https://developer.apple.com
2. Get a **Developer ID Application** certificate from Xcode or Apple Developer portal
3. Sign the nested FFmpeg binaries first, then the app bundle with hardened runtime:
   ```bash
   codesign -s "Developer ID Application: Your Name" --options runtime \
     YT\ Stream\ 24/7\ -\ Reencoder.app/Contents/MacOS/ffmpeg-apps/*
   codesign -s "Developer ID Application: Your Name" --options runtime \
     YT\ Stream\ 24/7\ -\ Reencoder.app
   ```
4. Notarize the DMG:
   ```bash
   xcrun notarytool submit YT-FFmpeg-Stream-Reencoder-macOS.dmg \
     --apple-id your@email.com --team-id YOURTEAMID --password app-specific-pw --wait
   ```
5. Staple the ticket:
   ```bash
   xcrun stapler staple YT-FFmpeg-Stream-Reencoder-macOS.dmg
   ```

After this, users can double-click the app normally with no warnings.

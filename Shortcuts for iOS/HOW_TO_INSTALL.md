# Installing a .shortcut File on iPhone

## Step 1 — Regenerate the file (if needed)
If `WiFi_QR_Code.shortcut` is missing or you've updated the generator:
```
cd "Shortcuts for iOS"
py generate_shortcut.py
```

## Step 2 — Transfer to iPhone

**Option A: AirDrop (easiest)**
1. Make sure your iPhone has AirDrop on (Control Center → AirDrop → Everyone or Contacts Only)
2. Right-click `WiFi_QR_Code.shortcut` in File Explorer
3. Select **Show more options** → **Share** → **AirDrop**
4. Select your iPhone from the list
5. Accept the transfer on your iPhone

**Option B: iCloud Drive**
1. Open iCloud Drive on your PC (or go to icloud.com → iCloud Drive)
2. Upload `WiFi_QR_Code.shortcut` to any folder
3. On iPhone, open the **Files** app → iCloud Drive
4. Tap the `.shortcut` file

**Option C: Email / Messages**
1. Email or iMessage the `.shortcut` file to yourself
2. Open the attachment on your iPhone and tap it

## Step 3 — Import into Shortcuts
1. When you tap the `.shortcut` file on your iPhone, the **Shortcuts** app opens automatically
2. A preview card appears showing the shortcut actions
3. Tap **Add Shortcut**
4. The shortcut now appears in your Shortcuts library

## Step 4 — Run the shortcut
1. Open **Shortcuts** app → tap **Wi-Fi Network Name (SSID)**
   *(or ask Siri: "Hey Siri, Wi-Fi Network Name")*
2. Enter your Wi-Fi network name when prompted
3. Enter your Wi-Fi password when prompted
4. A QR code image appears — anyone can scan it with their camera to join the network

## Notes
- The shortcut requires an internet connection to fetch the QR image (uses api.qrserver.com)
- Works with WPA/WPA2 networks; not designed for open (no-password) networks
- To share with guests: run the shortcut, then let them scan the Quick Look image with their camera app

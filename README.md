# WhatsApp Number Filter (Web Automation, Cross‑Platform)

This tool checks which phone numbers are registered on **WhatsApp** by automating **WhatsApp Web** with Selenium.  
It works on **Windows, macOS, and Linux**, and supports **Chrome, Firefox, and Edge**.

> ⚠️ **Important Disclaimer**  
> This project uses **web automation** against **WhatsApp Web**, which is likely **against WhatsApp’s Terms of Service** and may lead to:
> - Temporary or permanent **bans** of your WhatsApp account  
> - Other restrictions from WhatsApp  
>
> Use this project **at your own risk**, only for educational / experimental purposes.  
> For production or compliant use, you should use the **official WhatsApp Business API**.

---

## Features

- ✅ Check if phone numbers are **registered on WhatsApp** by opening each number in WhatsApp Web.
- ✅ **Cross‑platform**: Windows, macOS, Linux (Python + Selenium).
- ✅ **Multiple browsers**:
  - `chrome`
  - `firefox`
  - `edge`
- ✅ **CLI interface**:
  - Specify input file with phone numbers.
  - Specify output paths for valid and invalid numbers.
  - Optional **headless** mode.
  - Configurable **delay** between checks.
  - Optional **custom WebDriver path** (`--driver-path`).
- ✅ Automatic WebDriver download via `webdriver_manager` (when `--driver-path` is not given).
- ✅ Detailed fallback instructions if WebDriver cannot be created.
- ✅ Automatically saves:
  - **Valid numbers** to a file.
  - **Invalid numbers** to a file.

---

## Requirements

- **Python** 3.8+
- One of the supported browsers installed:
  - **Google Chrome**
  - **Mozilla Firefox**
  - **Microsoft Edge**

### Python dependencies

Use the included `requirements.txt` if you need version specific python modules use example below:

```text
selenium==4.25.0
webdriver-manager==4.0.2
```
Install them with:
```text
pip install -r requirements.txt
```
If you don’t want pinned versions, you can simplify requirements.txt to:
```text
selenium
webdriver-manager
```

---

## File Structure (Suggested)
You can organize your project like this:
```text
project-root/
├─ whatsapp_web_filter_cli.py
├─ requirements.txt
└─ data/
   ├─ input_numbers.txt
   ├─ valid_numbers.txt      # generated
   └─ invalid_numbers.txt    # generated
```
You can change file paths via CLI arguments.

---

## How It Works
1. You run the CLI script with an input file containing phone numbers (one per line, e.g. +923001234567).
2. The script:
   - Starts a browser (Chrome/Firefox/Edge) using Selenium.
   - Opens WhatsApp Web and waits for you to scan the QR code (only first time, session is reused).
3. For each phone number:
   - It opens:
     https://web.whatsapp.com/send?phone=<E164_NUMBER>&text=&type=phone_number&app_absent=0
   - It waits for WhatsApp Web to respond and then:
     - If a chat window opens → marks number as valid (registered).
     - If an error dialog appears (e.g. “phone number shared via url is invalid”) → marks number as invalid/unregistered.
4. At the end:
   - It automatically writes all valid numbers to the valid output file.
   - It automatically writes all invalid numbers to the invalid output file.
No manual saving step is required; it auto-saves when the run finishes.

---

**Usage**
**1. Install dependencies**
```text
pip install -r requirements.txt
```
**2. Prepare Input File**
Create data/input_numbers.txt with one phone number per line, preferably in international format:
```text
+923001234567
+923001234568
+923001234569
```
No extra spaces; + is allowed.
---
**3. Basic Command (Chrome, Auto Driver)**
```text
python whatsapp_web_filter_cli.py -i data/input_numbers.txt
```
This will:
- Use Chrome (default).
- Try to auto-download ChromeDriver using webdriver_manager.
- Auto-save:
  - Valid numbers to data/valid_numbers.txt
  - Invalid numbers to data/invalid_numbers.txt
---
**4. Choose Browser**
**Chrome (default)**
```text
python whatsapp_web_filter_cli.py -i data/input_numbers.txt --browser chrome
```
**Firefox**
```text
python whatsapp_web_filter_cli.py -i data/input_numbers.txt --browser firefox
```
**Edge**
```text
python whatsapp_web_filter_cli.py -i data/input_numbers.txt --browser edge
```
---
**5. Custom Output Paths**
```text
python whatsapp_web_filter_cli.py \
  -i data/input_numbers.txt \
  --valid-output results/whatsapp_valid.txt \
  --invalid-output results/whatsapp_invalid.txt
```
After the run:
- results/whatsapp_valid.txt will contain all valid WhatsApp numbers.
- results/whatsapp_invalid.txt will contain all invalid/unregistered numbers.
---
**6. Headless Mode**
Headless mode runs the browser without visible UI.
Note: Logging in by scanning QR code is harder or impossible in strict headless mode.
Normally you:
- Run once without --headless to log in and create a saved profile.
- Then use --headless for subsequent runs.
```text
python whatsapp_web_filter_cli.py -i data/input_numbers.txt --headless
```
---
**7. Delay Between Checks**
Increase the delay to be more gentle and reduce risk of rate limiting:
```text
python whatsapp_web_filter_cli.py -i data/input_numbers.txt --delay 4
```
This waits 4 seconds after each number check.

---

**8. Using a Custom WebDriver Path (--driver-path)**
If you have manually downloaded a driver:
**Windows example (Chrome)**
```text
python whatsapp_web_filter_cli.py \
  -i data/input_numbers.txt \
  --browser chrome \
  --driver-path "C:\WebDrivers\chromedriver.exe"
```
Linux/macOS example (Firefox)
```text
python whatsapp_web_filter_cli.py \
  -i data/input_numbers.txt \
  --browser firefox \
  --driver-path /usr/local/bin/geckodriver
```
When --driver-path is provided:
- The script uses that file directly.
- webdriver_manager is not used for that run.
---
## WebDriver Setup Details
If automatic driver setup fails, the script prints instructions and links.
Here’s a summary:

**ChromeDriver (for Chrome)**
- Download:
  https://chromedriver.chromium.org/downloads
- Steps:
  1. Check your Chrome version: chrome://settings/help.
  2. Download the matching ChromeDriver for your OS.
  3. Extract the binary (chromedriver / chromedriver.exe).
**GeckoDriver (for Firefox)**
- Download:
  https://github.com/mozilla/geckodriver/releases
- Steps:
  1. Download the latest release for your OS/architecture.
  2. Extract geckodriver / geckodriver.exe.
**Edge WebDriver (for Edge)**
- Download:
  https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/
- Steps:
  1. Check Edge version: edge://settings/help.
  2. Download the matching Edge WebDriver.
  3. Extract msedgedriver / msedgedriver.exe.
**Add to PATH (summary)**
- **Windows:**
  - Place driver in e.g. C:\WebDrivers\.
  - Add that folder to PATH (System Properties → Environment Variables).
- **macOS / Linux:**
  - Move driver to /usr/local/bin or any folder already in PATH:
  ```text
  sudo mv chromedriver /usr/local/bin/
  sudo chmod +x /usr/local/bin/chromedriver
  ```
  Or just use --driver-path to point directly to the driver file.
---
## Data Format
**Input**
- Text file, UTF-8.
- One phone number per line.
- Example:
```text
+923001234567
923001234568
+1 555 123 4567
```
The script:
- Strips whitespace.
- Removes duplicates.
- Accepts + sign and spaces; they are sanitized before querying.
## Output (Auto-Saved)
Two files:
- **Valid numbers**: all numbers that appeared to open a WhatsApp chat.
- **Invalid numbers**: all numbers that triggered an error or timeout.
By default:
- Valid → data/valid_numbers.txt
- Invalid → data/invalid_numbers.txt
You can change these with --valid-output and --invalid-output.
Both are plain text, one number per line.
---
## Script Reference
Main script: whatsapp_web_filter_cli.py
Key arguments:
- -i, --input (required): path to input file with phone numbers.
- --valid-output: path to valid numbers file (default: data/valid_numbers.txt).
- --invalid-output: path to invalid numbers file (default: data/invalid_numbers.txt).
- --browser: chrome | firefox | edge (default: chrome).
- --driver-path: custom path to WebDriver executable (optional).
- --headless: run browser in headless mode.
- --delay: delay between checks in seconds (default: 2.0).
The script:
- Creates a WebDriver with create_driver(...).
- Waits for login with wait_for_login(...).
- Processes all numbers with filter_numbers(...).
- Auto-saves the results.
---
## Notes, Limitations & Tips
- Selectors can break
  If WhatsApp changes its HTML structure (CSS selectors / text), the script may stop detecting:
  - Error dialogs, or
  - Chat headers.
In that case, you’ll need to update the XPaths/CSS selectors in the script.
- **False positives / negatives**
  This method is heuristic and depends on the UI; it is not guaranteed accurate.
- **Rate limiting & bans**
  - Use a reasonable delay (--delay), especially for large lists.
  - Do not run multiple instances in parallel on the same account.
  - Avoid thousands of checks in a very short time.
- **QR login & sessions**
  - For Chrome and Edge, the script uses a user-data-dir profile folder:
    - ./chrome_whatsapp_profile_chrome
    - ./edge_whatsapp_profile
- This allows your WhatsApp Web session to persist across runs.
- For Firefox, persistence may depend on how Firefox profiles are handled on your system.
---
## Example Commands Recap
```text
# Basic usage, Chrome, auto driver
python whatsapp_web_filter_cli.py -i data/input_numbers.txt

# Firefox, 4s delay
python whatsapp_web_filter_cli.py -i data/input_numbers.txt --browser firefox --delay 4

# Edge, custom driver path, custom outputs
python whatsapp_web_filter_cli.py \
  -i data/input_numbers.txt \
  --browser edge \
  --driver-path "C:\WebDrivers\msedgedriver.exe" \
  --valid-output results/valid.txt \
  --invalid-output results/invalid.txt

# Headless Chrome (after you already logged in once non-headless)
python whatsapp_web_filter_cli.py -i data/input_numbers.txt --headless
```
---
## Disclaimer
This project is not affiliated with, endorsed by, or supported by WhatsApp or Meta.
Educational Purpose Only.
All trademarks are property of their respective owners.
Use responsibly and at your own risk.

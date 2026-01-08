import argparse
import platform
import time
from pathlib import Path
from typing import List, Tuple, Optional

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# WebDriver manager imports
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager

from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService

WHATSAPP_WEB_URL = "https://web.whatsapp.com"


# ---------- File helpers ----------

def read_numbers_from_file(path: Path) -> List[str]:
    with path.open("r", encoding="utf-8") as f:
        lines = [line.strip() for line in f]

    seen = set()
    cleaned = []
    for line in lines:
        if not line:
            continue
        if line not in seen:
            seen.add(line)
            cleaned.append(line)
    return cleaned


def write_numbers(path: Path, numbers: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for n in numbers:
            f.write(n + "\n")


# ---------- WebDriver helpers ----------

def print_manual_driver_instructions(browser: str) -> None:
    os_name = platform.system()
    print("\n[INFO] Automatic WebDriver installation failed.")
    print(f"[INFO] Please install the {browser} WebDriver manually.\n")

    if browser == "chrome":
        print("ChromeDriver download:")
        print("  https://chromedriver.chromium.org/downloads")
        print("\nSteps:")
        print("  1) Check your Chrome version: chrome://settings/help")
        print("  2) Download the matching ChromeDriver for your OS.")
    elif browser == "firefox":
        print("GeckoDriver (Firefox) download:")
        print("  https://github.com/mozilla/geckodriver/releases")
        print("\nSteps:")
        print("  1) Download the latest geckodriver for your OS/architecture.")
    elif browser == "edge":
        print("Edge WebDriver (msedgedriver) download:")
        print("  https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/")
        print("\nSteps:")
        print("  1) Check your Edge version: edge://settings/help")
        print("  2) Download the matching Edge WebDriver for your OS.")

    print("\nAfter download:")
    if os_name == "Windows":
        print("  - Extract the driver (chromedriver.exe / geckodriver.exe / msedgedriver.exe)")
        print("  - Place it in a folder like C:\\WebDrivers\\")
        print("  - Add that folder to your PATH environment variable.")
        print("    Example (PowerShell, temporary):")
        print("      $env:PATH += ';C:\\WebDrivers'")
    elif os_name == "Darwin":  # macOS
        print("  - Extract the driver binary.")
        print("  - Move it to /usr/local/bin or another folder in your PATH.")
        print("    Example:")
        print("      sudo mv chromedriver /usr/local/bin/")
        print("      sudo chmod +x /usr/local/bin/chromedriver")
    else:  # Linux
        print("  - Extract the driver binary.")
        print("  - Move it to /usr/local/bin or /usr/bin (or any PATH folder).")
        print("    Example:")
        print("      sudo mv chromedriver /usr/local/bin/")
        print("      sudo chmod +x /usr/local/bin/chromedriver")

    print("\nOr re-run this script with --driver-path pointing to the driver file.")
    print("Example:")
    if os_name == "Windows":
        print("  python whatsapp_web_filter_cli.py -i input.txt --browser chrome --driver-path C:\\WebDrivers\\chromedriver.exe")
    else:
        print("  python whatsapp_web_filter_cli.py -i input.txt --browser chrome --driver-path /usr/local/bin/chromedriver")
    print()


def create_driver(browser: str, headless: bool = False, driver_path: Optional[str] = None) -> webdriver.Remote:
    """
    Create a Selenium WebDriver for the selected browser.
    If driver_path is provided, use that binary directly.
    Otherwise, use webdriver_manager to auto-download drivers.
    """
    try:
        if browser == "chrome":
            options = webdriver.ChromeOptions()
            options.add_argument("user-data-dir=./chrome_whatsapp_profile_chrome")
            if headless:
                options.add_argument("--headless=new")
                options.add_argument("--disable-gpu")
                options.add_argument("--window-size=1920,1080")

            if driver_path:
                service = ChromeService(executable_path=driver_path)
            else:
                service = ChromeService(ChromeDriverManager().install())

            driver = webdriver.Chrome(service=service, options=options)

        elif browser == "firefox":
            options = webdriver.FirefoxOptions()
            # This is just a logical profile name; Firefox may create it
            # differently; for simple use, session persistence may vary.
            if headless:
                options.headless = True

            if driver_path:
                service = FirefoxService(executable_path=driver_path)
            else:
                service = FirefoxService(GeckoDriverManager().install())

            driver = webdriver.Firefox(service=service, options=options)

        elif browser == "edge":
            options = webdriver.EdgeOptions()
            options.add_argument("user-data-dir=./edge_whatsapp_profile")
            if headless:
                options.add_argument("--headless=new")
                options.add_argument("--disable-gpu")
                options.add_argument("--window-size=1920,1080")

            if driver_path:
                service = EdgeService(executable_path=driver_path)
            else:
                service = EdgeService(EdgeChromiumDriverManager().install())

            driver = webdriver.Edge(service=service, options=options)

        else:
            raise ValueError(f"Unsupported browser: {browser}")

        return driver

    except (WebDriverException, Exception) as e:
        print(f"[ERROR] Failed to create WebDriver for {browser}: {e}")
        if not driver_path:
            # Only show auto-download instructions if user didn't specify a path
            print_manual_driver_instructions(browser)
        else:
            print("[INFO] You provided --driver-path, but launching the driver still failed.")
            print("[INFO] Make sure the path is correct and the file is executable.")
        raise SystemExit(1)


def wait_for_login(driver: webdriver.Remote, timeout: int = 120) -> None:
    print("[INFO] Waiting for WhatsApp Web login (scan the QR code if needed)...")
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div[data-testid='chat-list-search']")
            )
        )
    except TimeoutException:
        print("[ERROR] Timed out waiting for WhatsApp Web login.")
        raise
    print("[INFO] Logged into WhatsApp Web.")


def open_chat_for_number(
    driver: webdriver.Remote,
    phone_number: str,
    timeout: int = 20
) -> Tuple[bool, str]:
    """
    Try to open chat for a given phone number via URL.
    Return (is_registered, reason).
    """
    sanitized = phone_number.strip().replace("+", "").replace(" ", "")
    url = f"{WHATSAPP_WEB_URL}/send?phone={sanitized}&text=&type=phone_number&app_absent=0"
    driver.get(url)

    # Give WhatsApp time to redirect and render
    time.sleep(3)

    # 1) Look for an error dialog/text
    try:
        error_div = WebDriverWait(driver, 8).until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//*[contains(text(),'phone number shared via url is invalid') "
                    "or contains(text(),'couldn’t find this account') "
                    "or contains(text(),'couldn\\'t find this account') "
                    "or contains(text(),'invalid phone number')]"
                )
            )
        )
        if error_div:
            return False, "Error dialog: number invalid or not registered."
    except TimeoutException:
        # No error dialog detected (or text changed)
        pass

    # 2) Look for chat header (means chat opened)
    try:
        chat_header = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "header[data-testid='conversation-header']")
            )
        )
        if chat_header:
            return True, "Chat opened successfully (likely WhatsApp account)."
    except TimeoutException:
        return False, "Timeout waiting for chat UI (ambiguous; treating as invalid)."

    return False, "Unknown UI state (treating as invalid)."


def filter_numbers(
    driver: webdriver.Remote,
    numbers: List[str],
    per_number_delay: float
) -> Tuple[List[str], List[str]]:
    valid = []
    invalid = []

    total = len(numbers)
    for idx, num in enumerate(numbers, start=1):
        print(f"[INFO] Checking {idx}/{total}: {num}")
        is_registered, reason = open_chat_for_number(driver, num)
        print(f"       -> {reason}")
        if is_registered:
            valid.append(num)
        else:
            invalid.append(num)

        if per_number_delay > 0:
            time.sleep(per_number_delay)

    return valid, invalid


# ---------- CLI ----------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Filter WhatsApp-registered numbers using WhatsApp Web automation."
    )

    parser.add_argument(
        "-i",
        "--input",
        type=str,
        required=True,
        help="Input file path containing phone numbers (one per line).",
    )
    parser.add_argument(
        "--valid-output",
        type=str,
        default="data/valid_numbers.txt",
        help="Output file path for valid WhatsApp numbers (default: data/valid_numbers.txt).",
    )
    parser.add_argument(
        "--invalid-output",
        type=str,
        default="data/invalid_numbers.txt",
        help="Output file path for invalid/unregistered numbers (default: data/invalid_numbers.txt).",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode (note: QR login is harder in headless).",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=2.0,
        help="Delay in seconds between checks (default: 2.0). Increase to be safer.",
    )
    parser.add_argument(
        "--browser",
        type=str,
        choices=["chrome", "firefox", "edge"],
        default="chrome",
        help="Browser to use for automation: chrome, firefox, or edge (default: chrome).",
    )
    parser.add_argument(
        "--driver-path",
        type=str,
        default=None,
        help=(
            "Path to the WebDriver executable (chromedriver / geckodriver / msedgedriver). "
            "If not provided, webdriver_manager will try to auto-download the driver."
        ),
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    input_path = Path(args.input)
    valid_path = Path(args.valid_output)
    invalid_path = Path(args.invalid_output)

    if not input_path.exists():
        print(f"[ERROR] Input file not found: {input_path}")
        raise SystemExit(1)

    numbers = read_numbers_from_file(input_path)
    print(f"[INFO] Loaded {len(numbers)} numbers from {input_path}")
    print(f"[INFO] Using browser: {args.browser}")
    if args.driver_path:
        print(f"[INFO] Using custom driver path: {args.driver_path}")

    driver = create_driver(browser=args.browser, headless=args.headless, driver_path=args.driver_path)
    driver.get(WHATSAPP_WEB_URL)

    try:
        wait_for_login(driver)
        valid, invalid = filter_numbers(driver, numbers, args.delay)
    finally:
        driver.quit()

    write_numbers(valid_path, valid)
    write_numbers(invalid_path, invalid)

    print(f"[INFO] Done.")
    print(f"[INFO] Valid:   {len(valid)} -> {valid_path}")
    print(f"[INFO] Invalid: {len(invalid)} -> {invalid_path}")


if __name__ == "__main__":
    main()
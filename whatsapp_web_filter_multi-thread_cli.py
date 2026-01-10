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

from concurrent.futures import ThreadPoolExecutor, as_completed  # <<< ADDED

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

    # Ensure directory exists

    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:

        for n in numbers:

            f.write(n + "\n")

    print(f"[INFO] Wrote {len(numbers)} numbers to: {path.resolve()}")


def append_log(log_path: Path, text: str) -> None:

    log_path.parent.mkdir(parents=True, exist_ok=True)

    with log_path.open("a", encoding="utf-8") as f:

        f.write(text + "\n")


def append_number(path: Path, number: str) -> None:  # already added
    """
    Append a single number to the given file immediately.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(number + "\n")


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


def create_driver(  # uses profile_suffix for per-thread profiles
    browser: str,
    headless: bool = False,
    driver_path: Optional[str] = None,
    profile_suffix: Optional[str] = None,
) -> webdriver.Remote:
    """
    Create a Selenium WebDriver for the selected browser.

    profile_suffix is used to create a unique profile directory per thread.
    """

    base_profile_dir = Path.cwd() / "browser_profiles"
    base_profile_dir.mkdir(exist_ok=True)

    if profile_suffix is None:
        profile_suffix = "main"

    try:

        if browser == "chrome":

            options = webdriver.ChromeOptions()

            chrome_profile_dir = base_profile_dir / f"chrome_whatsapp_profile_{profile_suffix}"
            chrome_profile_dir.mkdir(exist_ok=True)

            options.add_argument(f"user-data-dir={chrome_profile_dir.resolve()}")

            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")

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

            firefox_profile_dir = base_profile_dir / f"firefox_whatsapp_profile_{profile_suffix}"
            firefox_profile_dir.mkdir(exist_ok=True)

            # For deeper Firefox profile control you could use FirefoxProfile

            if headless:
                options.headless = True

            if driver_path:
                service = FirefoxService(executable_path=driver_path)
            else:
                service = FirefoxService(GeckoDriverManager().install())

            driver = webdriver.Firefox(service=service, options=options)

        elif browser == "edge":

            options = webdriver.EdgeOptions()

            edge_profile_dir = base_profile_dir / f"edge_whatsapp_profile_{profile_suffix}"
            edge_profile_dir.mkdir(exist_ok=True)

            options.add_argument(f"user-data-dir={edge_profile_dir.resolve()}")

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

            print_manual_driver_instructions(browser)

        else:

            print("[INFO] You provided --driver-path, but launching the driver still failed.")
            print("[INFO] Make sure the path is correct and the file is executable.")

        raise SystemExit(1)


def wait_for_login(driver: webdriver.Remote, timeout: int = 180) -> None:

    print("[INFO] Waiting for WhatsApp Web login (scan the QR code if needed)...")

    end_time = time.time() + timeout

    last_state = None

    while time.time() < end_time:

        try:

            qr_elements = driver.find_elements(By.CSS_SELECTOR, "canvas[aria-label='Scan me!']")
            qr_containers = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='qrcode']")

            app_root = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='app']")
            chat_list = driver.find_elements(By.CSS_SELECTOR, "div[aria-label='Chats'], div[aria-label='Chat list']")
            conversation_header = driver.find_elements(By.CSS_SELECTOR, "header[data-testid='conversation-header']")

            if qr_elements or qr_containers:

                if last_state != "qr":

                    print("[DEBUG] QR code detected, waiting for you to scan...")
                    last_state = "qr"

            if app_root or chat_list or conversation_header:

                print("[INFO] Logged into WhatsApp Web (main UI detected).")
                return

        except Exception:
            pass

        time.sleep(1)

    print("[ERROR] Timed out waiting for WhatsApp Web login.")

    try:

        driver.save_screenshot("whatsapp_login_timeout.png")
        print("[INFO] Saved screenshot: whatsapp_login_timeout.png")

    except Exception as e:

        print(f"[WARN] Could not save screenshot: {e}")

    raise TimeoutException("WhatsApp Web login not detected in time")


def open_chat_for_number(

    driver: webdriver.Remote,

    phone_number: str,

    timeout: int = 15

) -> Tuple[bool, str]:

    sanitized = phone_number.strip().replace("+", "").replace(" ", "")

    url = f"{WHATSAPP_WEB_URL}/send?phone={sanitized}&text=&type=phone_number&app_absent=0"

    driver.get(url)

    time.sleep(3)

    invalid_modal_xpath = (

        "//div[@data-animate-modal-popup='true' and "

        "contains(@aria-label, 'Phone number shared via url is invalid')]"

        " | "

        "//div[@data-animate-modal-body='true']"

        "[.//div[contains(normalize-space(.), 'Phone number shared via url is invalid.')]]"

    )

    try:

        invalid_modal = WebDriverWait(driver, 7).until(
            EC.presence_of_element_located((By.XPATH, invalid_modal_xpath))
        )

        if invalid_modal:

            print("[DEBUG] Exact invalid-number modal detected for:", phone_number)

            return False, "Invalid popup detected: phone number shared via url is invalid."

    except TimeoutException:

        print("[DEBUG] No invalid popup detected for:", phone_number)

        return True, "No invalid popup detected within timeout: treating as valid."

    except Exception as e:

        print(f"[WARN] Error while checking for invalid popup: {e}")

        return False, f"Error while checking popup: {e!r}"

    print("[DEBUG] Reached fallback path for:", phone_number)

    return False, "Fallback path reached: treating as invalid."


# ---------- Single-driver mode helper ----------

def filter_numbers_single(   # <<< ADDED
    driver: webdriver.Remote,
    numbers: List[str],
    per_number_delay: float,
    valid_path: Path,
    invalid_path: Path,
) -> Tuple[List[str], List[str]]:

    valid: List[str] = []
    invalid: List[str] = []
    total = len(numbers)

    for idx, num in enumerate(numbers, start=1):

        print(f"[INFO] Checking {idx}/{total}: {num}")

        is_registered, reason = open_chat_for_number(driver, num)

        print(f"       -> {reason}")

        if is_registered:
            valid.append(num)
            append_number(valid_path, num)
        else:
            invalid.append(num)
            append_number(invalid_path, num)

        if per_number_delay > 0:
            time.sleep(per_number_delay)

    return valid, invalid


# ---------- Multithread helpers ----------

def chunk_list(lst: List[str], n: int):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def process_numbers_chunk(
    numbers_chunk: List[str],
    browser: str,
    headless: bool,
    driver_path: Optional[str],
    per_number_delay: float,
    valid_path: Path,
    invalid_path: Path,
    worker_id: int,
) -> Tuple[List[str], List[str]]:

    valid: List[str] = []
    invalid: List[str] = []

    profile_suffix = f"worker_{worker_id}"
    driver = create_driver(
        browser=browser,
        headless=headless,
        driver_path=driver_path,
        profile_suffix=profile_suffix,
    )
    driver.get(WHATSAPP_WEB_URL)

    try:
        wait_for_login(driver)
        total = len(numbers_chunk)

        for idx, num in enumerate(numbers_chunk, start=1):
            print(f"[THREAD {worker_id}] Checking {idx}/{total}: {num}")
            is_registered, reason = open_chat_for_number(driver, num)
            print(f"[THREAD {worker_id}]  -> {reason}")

            if is_registered:
                valid.append(num)
                append_number(valid_path, num)
            else:
                invalid.append(num)
                append_number(invalid_path, num)

            if per_number_delay > 0:
                time.sleep(per_number_delay)
    finally:
        driver.quit()

    return valid, invalid


def filter_numbers_threaded(
    numbers: List[str],
    per_number_delay: float,
    valid_path: Path,
    invalid_path: Path,
    browser: str,
    headless: bool,
    driver_path: Optional[str],
    max_workers: int = 2,
    chunk_size: int = 50,
) -> Tuple[List[str], List[str]]:

    all_valid: List[str] = []
    all_invalid: List[str] = []

    if not numbers:
        return all_valid, all_invalid

    chunks = list(chunk_list(numbers, chunk_size))

    print(f"[INFO] Total numbers: {len(numbers)} | "
          f"Chunks: {len(chunks)} | "
          f"Threads (max_workers): {max_workers} | "
          f"Chunk size: {chunk_size}")

    workers = min(max_workers, len(chunks))

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = []
        for worker_id, chunk in enumerate(chunks, start=1):
            futures.append(
                executor.submit(
                    process_numbers_chunk,
                    chunk,
                    browser,
                    headless,
                    driver_path,
                    per_number_delay,
                    valid_path,
                    invalid_path,
                    worker_id,
                )
            )

        for future in as_completed(futures):
            v, inv = future.result()
            all_valid.extend(v)
            all_invalid.extend(inv)

    return all_valid, all_invalid


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

    parser.add_argument(                 # <<< ADDED
        "--threads",
        type=int,
        default=2,
        help="Number of parallel browser threads to use in threaded mode (default: 2).",
    )

    parser.add_argument(                 # <<< ADDED
        "--chunk-size",
        type=int,
        default=50,
        help="How many numbers each thread processes per chunk in threaded mode (default: 50).",
    )

    parser.add_argument(                 # <<< ADDED
        "--mode",
        type=str,
        choices=["single", "threaded"],
        default="single",
        help="Execution mode: 'single' for one browser, 'threaded' for multiple browsers (default: single).",
    )

    return parser.parse_args()


def main() -> None:

    args = parse_args()

    cwd = Path.cwd()

    print(f"[INFO] Current working directory: {cwd}")

    input_path = Path(args.input)

    valid_path = Path(args.valid_output)

    invalid_path = Path(args.invalid_output)

    log_path = cwd / "run_log.txt"

    print(f"[INFO] Input file: {input_path.resolve()}")

    print(f"[INFO] Valid output will be: {valid_path.resolve()}")

    print(f"[INFO] Invalid output will be: {invalid_path.resolve()}")

    if not input_path.exists():

        print(f"[ERROR] Input file not found: {input_path}")
        raise SystemExit(1)

    numbers = read_numbers_from_file(input_path)

    print(f"[INFO] Loaded {len(numbers)} numbers from {input_path}")
    print(f"[INFO] Using browser: {args.browser}")
    print(f"[INFO] Mode: {args.mode}")

    if args.driver_path:
        print(f"[INFO] Using custom driver path: {args.driver_path}")

    if args.mode == "single":  # <<< ADDED: single-driver path

        driver = create_driver(
            browser=args.browser,
            headless=args.headless,
            driver_path=args.driver_path,
            profile_suffix="single",
        )
        driver.get(WHATSAPP_WEB_URL)

        try:
            wait_for_login(driver)
            valid, invalid = filter_numbers_single(
                driver=driver,
                numbers=numbers,
                per_number_delay=args.delay,
                valid_path=valid_path,
                invalid_path=invalid_path,
            )
        finally:
            driver.quit()

    else:  # threaded mode

        valid, invalid = filter_numbers_threaded(
            numbers=numbers,
            per_number_delay=args.delay,
            valid_path=valid_path,
            invalid_path=invalid_path,
            browser=args.browser,
            headless=args.headless,
            driver_path=args.driver_path,
            max_workers=args.threads,
            chunk_size=args.chunk_size,
        )

    # Final overwrite with clean deduplicated lists
    write_numbers(valid_path, valid)
    write_numbers(invalid_path, invalid)

    summary = (
        f"Run finished: {time.strftime('%Y-%m-%d %H:%M:%S')} | "
        f"Mode: {args.mode} | "
        f"Input: {input_path.resolve()} | "
        f"Valid: {len(valid)} -> {valid_path.resolve()} | "
        f"Invalid: {len(invalid)} -> {invalid_path.resolve()}"
    )

    append_log(log_path, summary)

    print(f"[INFO] {summary}")
    print(f"[INFO] Log appended to: {log_path.resolve()}")


if __name__ == "__main__":

    main()
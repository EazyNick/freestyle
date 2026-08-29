import os
import sys
import time
import logging
from pathlib import Path

import pyautogui
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / "env.env"


def setup_logger(log_file: Path) -> logging.Logger:
    logger = logging.getLogger("image_clicker")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


def get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def get_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return float(value)


def get_image_files(folder: Path, extensions: set[str], order_mode: str) -> list[Path]:
    images = [
        file
        for file in folder.iterdir()
        if file.is_file() and file.suffix.lower().lstrip(".") in extensions
    ]

    if order_mode == "modified":
        return sorted(images, key=lambda file: (file.stat().st_mtime, file.name.lower()))

    return sorted(images, key=lambda file: file.name.lower())


def click_image(
    image_path: Path,
    confidence: float,
    retry_seconds: float,
    move_duration: float,
    dry_run: bool,
    logger: logging.Logger,
) -> bool:
    deadline = time.time() + retry_seconds
    attempt = 1

    while time.time() <= deadline:
        logger.info("Searching attempt %s for %s", attempt, image_path)
        try:
            location = pyautogui.locateCenterOnScreen(str(image_path), confidence=confidence)
        except pyautogui.ImageNotFoundException:
            location = None

        if location is not None:
            logger.info("FOUND %s at x=%s y=%s", image_path.name, location.x, location.y)
            if dry_run:
                logger.info("DRY_RUN enabled. Click skipped for %s", image_path.name)
            else:
                pyautogui.moveTo(location.x, location.y, duration=move_duration)
                pyautogui.click()
                logger.info("CLICKED %s", image_path.name)
            return True

        attempt += 1
        time.sleep(0.3)

    logger.warning("MISS %s was not found for %.1fs", image_path.name, retry_seconds)
    return False


def resolve_target_folders(image_root: Path, target_folder: str, click_all_folders: bool) -> list[Path]:
    if click_all_folders:
        return sorted([path for path in image_root.iterdir() if path.is_dir()], key=lambda path: path.name.lower())

    folder = image_root / target_folder
    if not folder.exists() or not folder.is_dir():
        raise FileNotFoundError(f"Image folder not found: {folder}")

    return [folder]


def main() -> int:
    load_dotenv(ENV_PATH)

    log_file = BASE_DIR / os.getenv("LOG_FILE", "automation.log")
    logger = setup_logger(log_file)

    image_root = BASE_DIR / os.getenv("IMAGE_ROOT", "img")
    target_folder = os.getenv("TARGET_FOLDER", "Emblem_Card")
    click_all_folders = get_bool("CLICK_ALL_FOLDERS", False)
    loop_forever = get_bool("LOOP_FOREVER", True)
    confidence = get_float("CONFIDENCE", 0.85)
    retry_seconds = get_float("RETRY_SECONDS", 5.0)
    click_interval = get_float("CLICK_INTERVAL", 1.0)
    start_delay = get_float("START_DELAY", 3.0)
    move_duration = get_float("MOVE_DURATION", 0.1)
    dry_run = get_bool("DRY_RUN", False)
    order_mode = os.getenv("ORDER_MODE", "name").strip().lower()
    extensions = {
        ext.strip().lower().lstrip(".")
        for ext in os.getenv("IMAGE_EXTENSIONS", "png,jpg,jpeg,bmp").split(",")
        if ext.strip()
    }

    if not image_root.exists() or not image_root.is_dir():
        raise FileNotFoundError(f"Image root not found: {image_root}")

    if order_mode not in {"name", "modified"}:
        raise ValueError("ORDER_MODE must be either 'name' or 'modified'")

    pyautogui.FAILSAFE = get_bool("FAILSAFE", True)
    pyautogui.PAUSE = get_float("PYAUTOGUI_PAUSE", 0.05)

    logger.info("Loaded env from %s", ENV_PATH)
    logger.info("Logging to %s", log_file)
    logger.info(
        "Settings: image_root=%s target_folder=%s click_all_folders=%s loop_forever=%s "
        "order_mode=%s confidence=%.2f retry_seconds=%.1f click_interval=%.1f dry_run=%s failsafe=%s",
        image_root,
        target_folder,
        click_all_folders,
        loop_forever,
        order_mode,
        confidence,
        retry_seconds,
        click_interval,
        dry_run,
        pyautogui.FAILSAFE,
    )
    logger.info("Starting in %.1fs. Press Ctrl+C or move the mouse to a screen corner to stop.", start_delay)
    time.sleep(start_delay)

    clicked_count = 0
    missed_count = 0
    cycle = 1

    while True:
        logger.info("Cycle %s started", cycle)
        folders = resolve_target_folders(image_root, target_folder, click_all_folders)

        for folder in folders:
            images = get_image_files(folder, extensions, order_mode)
            if not images:
                logger.warning("SKIP no images found in %s", folder)
                continue

            logger.info("FOLDER %s has %s image(s): %s", folder.name, len(images), ", ".join(image.name for image in images))
            for image_path in images:
                if click_image(image_path, confidence, retry_seconds, move_duration, dry_run, logger):
                    clicked_count += 1
                else:
                    missed_count += 1
                logger.info("Waiting %.1fs before next image", click_interval)
                time.sleep(click_interval)

        logger.info("Cycle %s finished. total_clicked=%s total_missed=%s", cycle, clicked_count, missed_count)
        if not loop_forever:
            break
        cycle += 1

    logger.info("Done. clicked=%s missed=%s", clicked_count, missed_count)
    if missed_count:
        return 1

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyboardInterrupt, pyautogui.FailSafeException):
        print("\nStopped by user.")
        raise SystemExit(130)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)

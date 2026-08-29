import sys
from pathlib import Path

import pyautogui

from image_clicker.config import AppConfig
from image_clicker.logging_setup import LoggerFactory
from image_clicker.repository import ImageRepository
from image_clicker.runner import AutomationRunner
from image_clicker.screen import ScreenClicker


def main() -> int:
    base_dir = Path(__file__).resolve().parent
    config = AppConfig.from_env(base_dir)
    logger = LoggerFactory().create(config.log_file)
    image_repository = ImageRepository(config)
    screen_clicker = ScreenClicker(config, logger)
    runner = AutomationRunner(config, image_repository, screen_clicker, logger)
    return runner.run()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyboardInterrupt, pyautogui.FailSafeException):
        print("\nStopped by user.")
        raise SystemExit(130)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)

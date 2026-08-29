import logging
import time
from pathlib import Path

import pyautogui

from image_clicker.config import AppConfig


class ScreenClicker:
    def __init__(self, config: AppConfig, logger: logging.Logger) -> None:
        self.config = config
        self.logger = logger
        pyautogui.FAILSAFE = config.failsafe
        pyautogui.PAUSE = config.pyautogui_pause

    def click_image(self, image_path: Path) -> bool:
        deadline = time.time() + self.config.retry_seconds
        attempt = 1

        while time.time() <= deadline:
            self.logger.info("Searching attempt %s for %s", attempt, image_path)
            location = self._locate(image_path)

            if location is not None:
                self.logger.info("FOUND %s at x=%s y=%s", image_path.name, location.x, location.y)
                self._click(location.x, location.y, image_path.name)
                return True

            attempt += 1
            time.sleep(0.3)

        self.logger.warning("MISS %s was not found for %.1fs", image_path.name, self.config.retry_seconds)
        return False

    def _locate(self, image_path: Path):
        try:
            return pyautogui.locateCenterOnScreen(str(image_path), confidence=self.config.confidence)
        except pyautogui.ImageNotFoundException:
            return None

    def _click(self, x: int, y: int, image_name: str) -> None:
        if self.config.dry_run:
            self.logger.info("DRY_RUN enabled. Click skipped for %s", image_name)
            return

        pyautogui.moveTo(x, y, duration=self.config.move_duration)
        pyautogui.click()
        self.logger.info("CLICKED %s", image_name)

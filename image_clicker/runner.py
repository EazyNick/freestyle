import logging
import time

from image_clicker.config import AppConfig
from image_clicker.repository import ImageRepository
from image_clicker.screen import ScreenClicker


class AutomationRunner:
    def __init__(
        self,
        config: AppConfig,
        image_repository: ImageRepository,
        screen_clicker: ScreenClicker,
        logger: logging.Logger,
    ) -> None:
        self.config = config
        self.image_repository = image_repository
        self.screen_clicker = screen_clicker
        self.logger = logger
        self.clicked_count = 0
        self.missed_count = 0

    def run(self) -> int:
        self._log_startup()
        time.sleep(self.config.start_delay)

        cycle = 1
        while True:
            self.logger.info("Cycle %s started", cycle)
            self._run_cycle()
            self.logger.info(
                "Cycle %s finished. total_clicked=%s total_missed=%s",
                cycle,
                self.clicked_count,
                self.missed_count,
            )

            if not self.config.loop_forever:
                break

            cycle += 1

        self.logger.info("Done. clicked=%s missed=%s", self.clicked_count, self.missed_count)
        return 1 if self.missed_count else 0

    def _run_cycle(self) -> None:
        for folder in self.image_repository.target_folders():
            images = self.image_repository.image_files(folder)
            if not images:
                self.logger.warning("SKIP no images found in %s", folder)
                continue

            self.logger.info(
                "FOLDER %s has %s image(s): %s",
                folder.name,
                len(images),
                ", ".join(image.name for image in images),
            )
            for image_path in images:
                self._process_image(image_path)

    def _process_image(self, image_path) -> None:
        if self.screen_clicker.click_image(image_path):
            self.clicked_count += 1
        else:
            self.missed_count += 1

        self.logger.info("Waiting %.1fs before next image", self.config.click_interval)
        time.sleep(self.config.click_interval)

    def _log_startup(self) -> None:
        self.logger.info("Loaded env from %s", self.config.env_path)
        self.logger.info("Logging to %s", self.config.log_file)
        self.logger.info(
            "Settings: image_root=%s target_folder=%s click_all_folders=%s loop_forever=%s "
            "order_mode=%s confidence=%.2f retry_seconds=%.1f search_attempts_per_image=%s "
            "click_interval=%.1f dry_run=%s failsafe=%s",
            self.config.image_root,
            self.config.target_folder,
            self.config.click_all_folders,
            self.config.loop_forever,
            self.config.order_mode,
            self.config.confidence,
            self.config.retry_seconds,
            self.config.search_attempts_per_image,
            self.config.click_interval,
            self.config.dry_run,
            self.config.failsafe,
        )
        self.logger.info(
            "Starting in %.1fs. Press Ctrl+C or move the mouse to a screen corner to stop.",
            self.config.start_delay,
        )

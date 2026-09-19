import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class AppConfig:
    base_dir: Path
    env_path: Path
    image_root: Path
    target_folder: str
    click_all_folders: bool
    loop_forever: bool
    order_mode: str
    image_extensions: set[str]
    start_delay: float
    confidence: float
    retry_seconds: float
    search_attempts_per_image: int
    click_interval: float
    move_duration: float
    mouse_park_x: int
    mouse_park_y: int
    mouse_wiggle_pixels: int
    screen_refresh_delay: float
    pyautogui_pause: float
    dry_run: bool
    failsafe: bool
    log_file: Path

    @classmethod
    def from_env(cls, base_dir: Path, env_filename: str = "env.env") -> "AppConfig":
        env_path = base_dir / env_filename
        load_dotenv(env_path)

        config = cls(
            base_dir=base_dir,
            env_path=env_path,
            image_root=base_dir / os.getenv("IMAGE_ROOT", "img"),
            target_folder=os.getenv("TARGET_FOLDER", "Emblem_Card"),
            click_all_folders=_get_bool("CLICK_ALL_FOLDERS", False),
            loop_forever=_get_bool("LOOP_FOREVER", True),
            order_mode=os.getenv("ORDER_MODE", "name").strip().lower(),
            image_extensions=_get_extensions("IMAGE_EXTENSIONS", "png,jpg,jpeg,bmp"),
            start_delay=_get_float("START_DELAY", 3.0),
            confidence=_get_float("CONFIDENCE", 0.85),
            retry_seconds=_get_float("RETRY_SECONDS", 5.0),
            search_attempts_per_image=_get_int("SEARCH_ATTEMPTS_PER_IMAGE", 1),
            click_interval=_get_float("CLICK_INTERVAL", 1.0),
            move_duration=_get_float("MOVE_DURATION", 0.1),
            mouse_park_x=_get_int("MOUSE_PARK_X", 10),
            mouse_park_y=_get_int("MOUSE_PARK_Y", 500),
            mouse_wiggle_pixels=_get_int("MOUSE_WIGGLE_PIXELS", 1),
            screen_refresh_delay=_get_float("SCREEN_REFRESH_DELAY", 0.05),
            pyautogui_pause=_get_float("PYAUTOGUI_PAUSE", 0.05),
            dry_run=_get_bool("DRY_RUN", False),
            failsafe=_get_bool("FAILSAFE", True),
            log_file=base_dir / os.getenv("LOG_FILE", "automation.log"),
        )
        config.validate()
        return config

    def validate(self) -> None:
        if not self.image_root.exists() or not self.image_root.is_dir():
            raise FileNotFoundError(f"Image root not found: {self.image_root}")

        if self.order_mode not in {"name", "modified"}:
            raise ValueError("ORDER_MODE must be either 'name' or 'modified'")

        if self.search_attempts_per_image < 1:
            raise ValueError("SEARCH_ATTEMPTS_PER_IMAGE must be at least 1")

        if not self.image_extensions:
            raise ValueError("IMAGE_EXTENSIONS must include at least one extension")


def _get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _get_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return float(value)


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return int(value)


def _get_extensions(name: str, default: str) -> set[str]:
    return {
        ext.strip().lower().lstrip(".")
        for ext in os.getenv(name, default).split(",")
        if ext.strip()
    }

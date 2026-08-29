from pathlib import Path

from image_clicker.config import AppConfig


class ImageRepository:
    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def target_folders(self) -> list[Path]:
        if self.config.click_all_folders:
            return sorted(
                [path for path in self.config.image_root.iterdir() if path.is_dir()],
                key=lambda path: path.name.lower(),
            )

        folder = self.config.image_root / self.config.target_folder
        if not folder.exists() or not folder.is_dir():
            raise FileNotFoundError(f"Image folder not found: {folder}")

        return [folder]

    def image_files(self, folder: Path) -> list[Path]:
        images = [
            file
            for file in folder.iterdir()
            if file.is_file() and file.suffix.lower().lstrip(".") in self.config.image_extensions
        ]

        if self.config.order_mode == "modified":
            return sorted(images, key=lambda file: (file.stat().st_mtime, file.name.lower()))

        return sorted(images, key=lambda file: file.name.lower())

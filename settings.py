from pathlib import Path

# Дисплей
FPS: int = 60
SCREEN_W: int = 1280
SCREEN_H: int = 720
TITLE: str = "Evolution Z"

# Пути
BASE_DIR: Path = Path(__file__).parent
ASSETS_DIR: Path = BASE_DIR / "assets"
DATA_DIR: Path = ASSETS_DIR / "data"
MAPS_DIR: Path = ASSETS_DIR / "maps"
SPRITES_DIR: Path = ASSETS_DIR / "sprites"
SOUNDS_DIR: Path = ASSETS_DIR / "sounds"
SAVES_DIR: Path = BASE_DIR / "saves"

# Цвета
BLACK: tuple[int, int, int] = (0, 0, 0)
WHITE: tuple[int, int, int] = (255, 255, 255)
DARK_GRAY: tuple[int, int, int] = (30, 30, 30)

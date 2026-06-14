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

# Босс
BOSS_MAX_HEALTH: int = 600
# AI босса (Sprint 9D). Минимальные функциональные значения, не балансировка.
BOSS_SPEED: float = 90.0
BOSS_DETECTION_RANGE: float = 400.0
BOSS_ATTACK_RANGE: float = 70.0
BOSS_ATTACK_COOLDOWN: float = 1.2
BOSS_DAMAGE: float = 20.0
# Фаза 2 (агрессивная) при HP <= доли от максимума: быстрее и чаще бьёт.
BOSS_PHASE2_HEALTH_FRACTION: float = 0.5
BOSS_PHASE2_SPEED_MULTIPLIER: float = 1.5
BOSS_PHASE2_COOLDOWN_MULTIPLIER: float = 0.6
# Кислотная спец-атака фазы 2 (Sprint 9E). Отдельный кулдаун; минимальные
# функциональные значения, не балансировка. Снаряд — существующий AcidBullet.
BOSS_ACID_COOLDOWN: float = 2.5
BOSS_ACID_DAMAGE: float = 15.0
BOSS_ACID_SPEED: float = 260.0
BOSS_ACID_RANGE: float = 500.0
BOSS_ACID_SIZE: int = 8
# Призыв миньонов фазы 2 (Sprint 9F). Отдельный кулдаун и лимит одновременно живых;
# миньоны — существующий WalkerZombie, без новых типов/BossData/JSON.
BOSS_SUMMON_COOLDOWN: float = 6.0
BOSS_SUMMON_MAX: int = 3

# Тайлы
TILE_SIZE: int = 32
TILE_FLOOR_COLOR: tuple[int, int, int] = (45, 45, 55)
TILE_WALL_COLOR: tuple[int, int, int] = (75, 75, 95)

# Цвета
BLACK: tuple[int, int, int] = (0, 0, 0)
WHITE: tuple[int, int, int] = (255, 255, 255)
DARK_GRAY: tuple[int, int, int] = (30, 30, 30)

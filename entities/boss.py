from __future__ import annotations

import pygame

from core.entity import Entity
from data.enemy_data import EnemyData
from entities.bullet import AcidBullet, Bullet
from entities.zombie import WalkerZombie, Zombie
from settings import (
    BOSS_ACID_COOLDOWN,
    BOSS_ACID_DAMAGE,
    BOSS_ACID_RANGE,
    BOSS_ACID_SIZE,
    BOSS_ACID_SPEED,
    BOSS_ATTACK_COOLDOWN,
    BOSS_ATTACK_RANGE,
    BOSS_DAMAGE,
    BOSS_DETECTION_RANGE,
    BOSS_PATROL_ARRIVE_DIST,
    BOSS_PATROL_RADIUS,
    BOSS_PATROL_SPEED_FACTOR,
    BOSS_PHASE2_COOLDOWN_MULTIPLIER,
    BOSS_PHASE2_HEALTH_FRACTION,
    BOSS_PHASE2_SPEED_MULTIPLIER,
    BOSS_SPEED,
    BOSS_SUMMON_COOLDOWN,
    BOSS_SUMMON_MAX,
    BOSS_XP_REWARD,
    TILE_SIZE,
)
from systems.asset_loader import AssetLoader
from systems.event_bus import EventBus


class Boss(Entity):
    """Базовый класс боссов. Враждебная сущность с прямоугольником коллизий.

    Совместим с CombatSystem (Targetable): имеет active, pos, faction, rect, take_damage.
    Получает урон существующим способом (через Entity → HealthComponent). При гибели —
    помимо унаследованного `entity_died` — эмитит `boss_defeated` ровно один раз.
    """

    COLOR: tuple[int, int, int] = (120, 30, 120)
    SPRITE: str | None = None  # переопределяется подклассами; None → fallback-примитив
    # Босс — faction='enemy', значит проходит через путь начисления XP за врагов
    # (GameScreen._on_entity_died читает entity.xp_reward). Значение — из settings
    # (Sprint 9G), как у Zombie.xp_reward; без новой системы наград.
    xp_reward: int = BOSS_XP_REWARD

    def __init__(self, x: float, y: float, max_health: int, width: int, height: int) -> None:
        super().__init__(x, y, max_health)
        self.faction = "enemy"
        self._rect: pygame.Rect = pygame.Rect(0, 0, width, height)
        self._rect.center = (int(x), int(y))

    @property
    def rect(self) -> pygame.Rect:
        """Прямоугольник для коллизий и рендера."""
        return self._rect

    def take_damage(self, amount: float) -> None:
        """Получить урон существующим способом; при гибели эмитит `boss_defeated`.

        Делегирует `Entity.take_damage` (тот клампит HP, снимает active и эмитит
        `entity_died`), затем добавляет boss-специфичное событие строго на переходе
        жив→мёртв — поэтому ровно один раз, даже при повторных или избыточных попаданиях.
        """
        was_alive = self.is_alive
        super().take_damage(amount)
        if was_alive and not self.is_alive:
            EventBus.emit("boss_defeated", {"boss": self})

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        """Отрисовка спрайта (или fallback-примитива) босса с полоской HP."""
        draw_rect = self._rect.move(-int(offset.x), -int(offset.y))
        if not AssetLoader.draw_sprite(surface, self.SPRITE, draw_rect):
            pygame.draw.rect(surface, self.COLOR, draw_rect)

        bar_w = self._rect.width
        hp_w = max(0, int(bar_w * self.health.percentage))
        bar_y = draw_rect.y - 8
        pygame.draw.rect(surface, (60, 0, 0), (draw_rect.x, bar_y, bar_w, 5))
        pygame.draw.rect(surface, (200, 40, 200), (draw_rect.x, bar_y, hp_w, 5))


class PatientZeroBoss(Boss):
    """Носитель Ноль — финальный босс.

    AI зеркалит подход зомби: преследование игрока в радиусе обнаружения и ближняя атака
    по кулдауну (Sprint 9D). Две фазы — при HP <= 50% (фаза 2) босс быстрее и бьёт чаще.
    В фазе 2 при обнаруженном игроке также плюётся кислотой (Sprint 9E) и призывает
    миньонов (Sprint 9F), каждое — по своему кулдауну.
    """

    COLOR = (150, 20, 90)
    SPRITE = "boss"
    _SIZE: int = TILE_SIZE * 2  # босс крупнее обычных врагов; размер из settings, не магия

    def __init__(
        self,
        x: float,
        y: float,
        max_health: int,
        minion_config: EnemyData | None = None,
    ) -> None:
        super().__init__(x, y, max_health, self._SIZE, self._SIZE)
        self._attack_timer: float = 0.0
        self._acid_timer: float = 0.0
        self._summon_timer: float = 0.0
        self._pending_bullets: list[Bullet] = []
        # Конфиг призываемого миньона (инъекция из GameScreen). None → босс не призывает,
        # поэтому юнит-тесты `PatientZeroBoss(x, y, hp)` работают без изменений.
        self._minion_config: EnemyData | None = minion_config
        self._pending_minions: list[Zombie] = []
        # Ссылки на призванных — для учёта лимита одновременно живых (active).
        self._summoned: list[Zombie] = []
        # Патруль вне боя (Sprint 10A): несколько точек вокруг точки спавна (якоря).
        # Якорь фиксируется на старте — до любого движения. Точки обходятся циклически.
        r = BOSS_PATROL_RADIUS
        self._patrol_anchor: pygame.Vector2 = pygame.Vector2(self.pos)
        self._patrol_points: list[pygame.Vector2] = [
            pygame.Vector2(r, 0.0),
            pygame.Vector2(0.0, r),
            pygame.Vector2(-r, 0.0),
            pygame.Vector2(0.0, -r),
        ]
        self._patrol_index: int = 0

    # ── фазы ───────────────────────────────────────────────────────────────

    @property
    def phase(self) -> int:
        """Текущая фаза: 1 при HP > 50%, 2 (агрессивная) при HP <= 50%."""
        return 2 if self.health.percentage <= BOSS_PHASE2_HEALTH_FRACTION else 1

    @property
    def speed(self) -> float:
        """Текущая скорость движения; в фазе 2 выше."""
        multiplier = BOSS_PHASE2_SPEED_MULTIPLIER if self.phase == 2 else 1.0
        return BOSS_SPEED * multiplier

    @property
    def attack_cooldown(self) -> float:
        """Текущий кулдаун атаки; в фазе 2 ниже (бьёт чаще)."""
        multiplier = BOSS_PHASE2_COOLDOWN_MULTIPLIER if self.phase == 2 else 1.0
        return BOSS_ATTACK_COOLDOWN * multiplier

    @property
    def can_attack(self) -> bool:
        """Готов ли босс к атаке (кулдаун истёк)."""
        return self._attack_timer <= 0.0

    @property
    def can_spit(self) -> bool:
        """Готов ли босс к кислотному плевку (отдельный кулдаун истёк)."""
        return self._acid_timer <= 0.0

    @property
    def can_summon(self) -> bool:
        """Готов ли босс призвать миньона: есть конфиг, кулдаун истёк, лимит живых не достигнут."""
        if self._minion_config is None or self._summon_timer > 0.0:
            return False
        return self._active_minions() < BOSS_SUMMON_MAX

    def _active_minions(self) -> int:
        """Число ещё живых призванных миньонов (для лимита одновременности)."""
        return sum(1 for m in self._summoned if m.active)

    # ── AI (структура как у Zombie.update_ai) ──────────────────────────────

    def update(
        self,
        dt: float,
        walls: list[pygame.Rect] | None = None,
        player: Entity | None = None,
    ) -> None:
        """Тик AI: декремент кулдауна, затем преследование / ближняя атака.

        Сигнатура совпадает с `Zombie.update` (walls/player опциональны), поэтому
        вызывается как обычный враг: `boss.update(dt, walls, player)`.
        """
        self._attack_timer = max(0.0, self._attack_timer - dt)
        self._acid_timer = max(0.0, self._acid_timer - dt)
        self._summon_timer = max(0.0, self._summon_timer - dt)
        if player is None:
            return

        player_pos = player.pos
        # Phase 2 — только живой босс при ОБНАРУЖЕННОМ игроке: кислота и призыв миньонов,
        # каждый по своему кулдауну. _detect_player — тот же радиус, что у melee/преследования,
        # без отдельной системы агро. Гейт is_alive не даёт «мёртвому» боссу (0% HP → phase 2)
        # действовать, если update вызван после гибели. Melee ниже не меняется.
        if self.is_alive and self.phase == 2 and self._detect_player(player_pos):
            if self.can_spit:
                self.spit_acid(player)
                self._acid_timer = BOSS_ACID_COOLDOWN
            if self.can_summon:
                self.summon_minion()
                self._summon_timer = BOSS_SUMMON_COOLDOWN

        if self._in_attack_range(player_pos):
            if self.can_attack:
                self.attack(player)
                self._attack_timer = self.attack_cooldown
        elif self._detect_player(player_pos):
            self._move_toward(player_pos, walls or [], dt)
        else:
            # Игрок не обнаружен → патруль вне боя. Любое обнаружение выше немедленно
            # прерывает патруль (ветки melee/chase), потеря игрока — снова сюда.
            self._patrol(walls or [], dt)

    def attack(self, target: Entity) -> None:
        """Ближняя атака: урон по цели через её HealthComponent (как melee-зомби)."""
        target.take_damage(BOSS_DAMAGE)

    def spit_acid(self, target: Entity) -> None:
        """Кислотный плевок в направлении цели (Phase 2), зеркало SpitterZombie.attack.

        Снаряд — существующий AcidBullet с origin_tag='enemy' (CombatSystem не даст ему
        бить врагов/босса). Кладётся в очередь, которую сливает collect_spawned_bullets.
        Нулевое направление (цель в точке босса) — нет-оп.
        """
        direction = target.pos - self.pos
        if direction.length_squared() == 0:
            return
        direction.normalize_ip()
        bullet = AcidBullet(
            x=self.pos.x,
            y=self.pos.y,
            velocity=direction * BOSS_ACID_SPEED,
            damage=BOSS_ACID_DAMAGE,
            max_range=BOSS_ACID_RANGE,
            size=BOSS_ACID_SIZE,
            origin_tag="enemy",
        )
        self._pending_bullets.append(bullet)

    def collect_spawned_bullets(self) -> list[Bullet]:
        """Возвращает накопленные кислотные снаряды и очищает очередь (как SpitterZombie)."""
        bullets: list[Bullet] = list(self._pending_bullets)
        self._pending_bullets = []
        return bullets

    def summon_minion(self) -> None:
        """Призвать заражённого (WalkerZombie) рядом с боссом (Phase 2).

        Использует существующий тип врага и инъецированный конфиг — новых типов миньонов /
        BossData / JSON не вводится. Ссылка хранится для учёта лимита живых; очередь сливает
        collect_spawned_minions (паттерн collect_spawned_bullets). Нет-оп без конфига.
        """
        if self._minion_config is None:
            return
        # Прунинг мёртвых ссылок: список живых остаётся ограниченным (≤ BOSS_SUMMON_MAX),
        # не накапливая трупы. Лимит (can_summon) при этом не меняется.
        self._summoned = [m for m in self._summoned if m.active]
        minion = WalkerZombie(self.pos.x + TILE_SIZE, self.pos.y, self._minion_config)
        self._pending_minions.append(minion)
        self._summoned.append(minion)

    def collect_spawned_minions(self) -> list[Zombie]:
        """Возвращает призванных с последнего вызова миньонов и очищает очередь."""
        minions: list[Zombie] = list(self._pending_minions)
        self._pending_minions = []
        return minions

    # ── патруль вне боя (Sprint 10A) ───────────────────────────────────────

    @property
    def patrol_target(self) -> pygame.Vector2:
        """Текущая целевая точка патруля (якорь + смещение активной точки)."""
        return self._patrol_anchor + self._patrol_points[self._patrol_index]

    def _patrol(self, walls: list[pygame.Rect], dt: float) -> None:
        """Движение к текущей точке патруля; по достижении — переход к следующей.

        Скорость снижена `BOSS_PATROL_SPEED_FACTOR` (как у Zombie._patrol через dt*0.5),
        переиспользует `_move_toward` (коллизии стен). Точки обходятся циклически.
        """
        if self.pos.distance_to(self.patrol_target) <= BOSS_PATROL_ARRIVE_DIST:
            self._patrol_index = (self._patrol_index + 1) % len(self._patrol_points)
        self._move_toward(self.patrol_target, walls, dt * BOSS_PATROL_SPEED_FACTOR)

    # ── вспомогательные (зеркало Zombie) ───────────────────────────────────

    def _detect_player(self, player_pos: pygame.Vector2) -> bool:
        """True, если игрок в радиусе обнаружения."""
        return self.pos.distance_to(player_pos) <= BOSS_DETECTION_RANGE

    def _in_attack_range(self, player_pos: pygame.Vector2) -> bool:
        """True, если игрок достижим для ближней атаки."""
        return self.pos.distance_to(player_pos) <= BOSS_ATTACK_RANGE

    def _move_toward(
        self, target_pos: pygame.Vector2, walls: list[pygame.Rect], dt: float
    ) -> None:
        """Движение к target_pos с AABB-коллизиями стен (как Zombie._move_toward)."""
        direction = target_pos - self.pos
        if direction.length_squared() == 0:
            return
        direction.normalize_ip()
        speed = self.speed * dt

        self.pos.x += direction.x * speed
        self._rect.centerx = int(self.pos.x)
        self._resolve_x(walls)

        self.pos.y += direction.y * speed
        self._rect.centery = int(self.pos.y)
        self._resolve_y(walls)

        self.pos.x = float(self._rect.centerx)
        self.pos.y = float(self._rect.centery)

    def _resolve_x(self, walls: list[pygame.Rect]) -> None:
        for wall in walls:
            if self._rect.colliderect(wall):
                if self._rect.centerx > wall.centerx:
                    self._rect.left = wall.right
                else:
                    self._rect.right = wall.left
                self.pos.x = float(self._rect.centerx)

    def _resolve_y(self, walls: list[pygame.Rect]) -> None:
        for wall in walls:
            if self._rect.colliderect(wall):
                if self._rect.centery > wall.centery:
                    self._rect.top = wall.bottom
                else:
                    self._rect.bottom = wall.top
                self.pos.y = float(self._rect.centery)

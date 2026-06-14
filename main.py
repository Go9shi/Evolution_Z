import pygame

from settings import BLACK, FPS, SCREEN_H, SCREEN_W, TITLE
from ui.base_screen import BaseScreen


class GameStateManager:
    """Стек экранов. Активен только верхний — прочие заморожены."""

    def __init__(self) -> None:
        self._stack: list[BaseScreen] = []

    def push(self, screen: BaseScreen) -> None:
        """Поместить новый экран поверх стека."""
        self._stack.append(screen)

    def pop(self) -> None:
        """Убрать верхний экран, освободив его ресурсы (cleanup), и вернуться к предыдущему."""
        if self._stack:
            screen = self._stack.pop()
            screen.cleanup()

    @property
    def current(self) -> BaseScreen | None:
        """Активный экран или None, если стек пуст."""
        return self._stack[-1] if self._stack else None

    @property
    def depth(self) -> int:
        """Количество экранов в стеке."""
        return len(self._stack)

    @property
    def is_empty(self) -> bool:
        """Проверка, пуст ли стек."""
        return not self._stack


class Game:
    """Главный класс игры. Управляет циклом, окном и менеджером состояний."""

    def __init__(self) -> None:
        pygame.init()
        self._screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption(TITLE)
        self._clock = pygame.time.Clock()
        self._running = False
        self.state_manager = GameStateManager()

    def stop(self) -> None:
        """Завершить игровой цикл (используется пунктом Quit в Main Menu)."""
        self._running = False

    def run(self) -> None:
        """Запуск основного цикла игры."""
        self._running = True
        while self._running:
            dt = self._clock.tick(FPS) / 1000.0
            self._handle_events()
            self._update(dt)
            self._render()
        pygame.quit()

    def _handle_events(self) -> None:
        state = self.state_manager.current
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._running = False
                continue
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                # ESC отдаётся активному экрану: Main Menu игнорирует его, GameScreen
                # открывает паузу (push → depth растёт), оверлеи закрываются (pop).
                # Приложение завершается лишь если ESC нажат на корневом экране и тот
                # НЕ открыл ничего сверху (т.е. Main Menu), иначе пауза/закрытие оверлея.
                at_root = self.state_manager.depth <= 1
                if state:
                    state.handle_event(event)
                if at_root and self.state_manager.depth <= 1:
                    self._running = False
                continue
            if state:
                state.handle_event(event)

    def _update(self, dt: float) -> None:
        state = self.state_manager.current
        if state:
            state.update(dt)

    def _render(self) -> None:
        self._screen.fill(BLACK)
        state = self.state_manager.current
        if state:
            state.draw(self._screen)
        pygame.display.flip()


if __name__ == "__main__":
    from ui.main_menu import MainMenuScreen

    game = Game()
    game.state_manager.push(MainMenuScreen(game.state_manager, game.stop))
    game.run()

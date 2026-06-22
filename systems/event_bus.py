from typing import Any, Callable


class EventBus:
    """Глобальная шина событий. Системы связываются только через неё."""

    _listeners: dict[str, list[Callable[..., None]]] = {}

    @classmethod
    def on(cls, event: str, callback: Callable[..., None]) -> None:
        """Подписаться на событие."""
        cls._listeners.setdefault(event, []).append(callback)

    @classmethod
    def off(cls, event: str, callback: Callable[..., None]) -> None:
        """Отписаться от события."""
        if event in cls._listeners:
            cls._listeners[event].remove(callback)

    @classmethod
    def emit(cls, event: str, data: dict[str, Any] | None = None) -> None:
        """Эмитировать событие всем подписчикам."""
        for callback in cls._listeners.get(event, []):
            callback(data or {})

    @classmethod
    def clear(cls) -> None:
        """Очистить все подписки. Вызывать при смене сцены."""
        cls._listeners.clear()

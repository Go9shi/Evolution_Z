from dataclasses import dataclass


@dataclass
class LoreEntry:
    """Запись лора: фрагмент мира или сюжета, который игрок может открыть.

    id — уникальный идентификатор записи; title — заголовок; text — содержимое.
    category — опциональная группировка (напр. 'terminal', 'note'); пустая по умолчанию.
    Чистая модель данных: о механике открытия и хранении знает только LoreSystem.
    """

    id: str
    title: str
    text: str
    category: str = ""

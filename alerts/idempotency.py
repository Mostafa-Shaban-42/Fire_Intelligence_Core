from typing import Set

class IdempotencyManager:
    def __init__(self):
        self._processed_keys: Set[str] = set()

    def is_processed(self, idempotency_key: str) -> bool:
        if idempotency_key in self._processed_keys:
            return True
        self._processed_keys.add(idempotency_key)
        return False
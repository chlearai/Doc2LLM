from dataclasses import dataclass


@dataclass
class ConversionLimiter:
    max_active: int = 2
    max_pending: int = 10
    active_count: int = 0
    pending_count: int = 0

    def reserve_slot(self) -> str | None:
        if self.active_count < self.max_active:
            self.active_count += 1
            return "PROCESSING"
        if self.pending_count < self.max_pending:
            self.pending_count += 1
            return "PENDING"
        return None

    def release_pending(self) -> None:
        if self.pending_count > 0:
            self.pending_count -= 1

    def release_active(self) -> bool:
        if self.active_count > 0:
            self.active_count -= 1
        if self.pending_count > 0 and self.active_count < self.max_active:
            self.pending_count -= 1
            self.active_count += 1
            return True
        return False

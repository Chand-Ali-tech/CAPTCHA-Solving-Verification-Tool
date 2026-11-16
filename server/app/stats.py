"""
stats.py
========
In-memory running statistics for the reporting dashboard
(Rubric part D: "Display total attempts, successful and failed attempts,
processing time, challenge type, and provider or solving method").

Kept intentionally simple (a singleton in memory). In production you'd
persist this to a database; for an assessment demo, in-memory is clear
and dependency-free.
"""
from __future__ import annotations

import threading
from dataclasses import dataclass, field, asdict

from .config import CUSTOM_SOLVE_COST_USD


@dataclass
class Stats:
    total_attempts: int = 0
    successful: int = 0
    failed: int = 0
    total_time_ms: float = 0.0
    total_cost_usd: float = 0.0
    by_method: dict[str, int] = field(default_factory=dict)
    recent: list[dict] = field(default_factory=list)  # last N events

    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def record(self, *, success: bool, elapsed_ms: float, method: str,
               cost_usd: float = CUSTOM_SOLVE_COST_USD,
               detail: dict | None = None) -> None:
        with self._lock:
            self.total_attempts += 1
            self.successful += int(bool(success))
            self.failed += int(not success)
            self.total_time_ms += elapsed_ms
            self.total_cost_usd += cost_usd
            self.by_method[method] = self.by_method.get(method, 0) + 1
            event = {"success": success, "elapsed_ms": elapsed_ms,
                     "method": method, "cost_usd": cost_usd}
            if detail:
                event.update(detail)
            self.recent.insert(0, event)
            del self.recent[25:]  # keep only the 25 most recent

    def snapshot(self) -> dict:
        with self._lock:
            avg = (self.total_time_ms / self.total_attempts
                   if self.total_attempts else 0.0)
            acc = (self.successful / self.total_attempts
                   if self.total_attempts else 0.0)
            return {
                "total_attempts": self.total_attempts,
                "successful": self.successful,
                "failed": self.failed,
                "accuracy": round(acc, 4),
                "avg_time_ms": round(avg, 1),
                "total_time_ms": round(self.total_time_ms, 1),
                "total_cost_usd": round(self.total_cost_usd, 6),
                "by_method": dict(self.by_method),
                "recent": list(self.recent),
            }

    def reset(self) -> None:
        with self._lock:
            self.total_attempts = self.successful = self.failed = 0
            self.total_time_ms = self.total_cost_usd = 0.0
            self.by_method.clear()
            self.recent.clear()


# Module-level singleton shared across requests.
STATS = Stats()

"""Simple JSON-based storage for payment records."""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Optional


@dataclass
class PaymentRecord:
    payment_id: str
    telegram_id: int
    amount: float
    status: str
    confirmation_url: str


class PaymentStorage:
    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write({})

    def _read(self) -> Dict[str, PaymentRecord]:
        raw = json.loads(self.path.read_text())
        return {
            payment_id: PaymentRecord(**record)
            for payment_id, record in raw.items()
        }

    def _write(self, data: Dict[str, PaymentRecord]) -> None:
        serializable = {pid: asdict(record) for pid, record in data.items()}
        self.path.write_text(json.dumps(serializable, indent=2, ensure_ascii=False))

    def save(self, record: PaymentRecord) -> None:
        data = self._read()
        data[record.payment_id] = record
        self._write(data)

    def get(self, payment_id: str) -> Optional[PaymentRecord]:
        return self._read().get(payment_id)

    def update_status(self, payment_id: str, status: str) -> Optional[PaymentRecord]:
        data = self._read()
        record = data.get(payment_id)
        if not record:
            return None
        record.status = status
        data[payment_id] = record
        self._write(data)
        return record


"""YooKassa payment helper functions."""
from __future__ import annotations

import uuid
from typing import Optional

from yookassa import Configuration, Payment

from .config import BotSettings


class YooKassaGateway:
    def __init__(self, settings: BotSettings) -> None:
        Configuration.account_id = settings.yookassa_shop_id
        Configuration.secret_key = settings.yookassa_secret_key
        self.amount = settings.plan_price

    def create_payment(self, description: str, metadata: Optional[dict] = None) -> Payment:
        payment = Payment.create(
            {
                "amount": {"value": f"{self.amount:.2f}", "currency": "RUB"},
                "confirmation": {
                    "type": "redirect",
                    "return_url": metadata.get("return_url") if metadata else None,
                },
                "capture": True,
                "description": description,
                "metadata": metadata or {},
            },
            uuid.uuid4(),
        )
        return payment

    def fetch_payment(self, payment_id: str) -> Payment:
        return Payment.find_one(payment_id)


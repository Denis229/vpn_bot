"""Client for interacting with the 3x-ui panel API."""
from __future__ import annotations

import datetime as dt
import uuid
from typing import Any, Dict

import requests

from .config import BotSettings, VpnUser


class VpnApiError(RuntimeError):
    pass


class VpnPanelClient:
    """HTTP client for the 3x-ui panel API."""

    def __init__(self, settings: BotSettings) -> None:
        self.settings = settings
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {settings.panel_api_key}"})

    def _url(self, path: str) -> str:
        return f"{self.settings.panel_base_url.rstrip('/')}{path}"

    def create_user(self, telegram_id: int) -> VpnUser:
        """Creates a new VPN user on the panel and returns connection details."""

        expire = int((dt.datetime.utcnow() + dt.timedelta(days=self.settings.days_valid)).timestamp())
        traffic = self.settings.traffic_gb * 1024 * 1024 * 1024
        remark = f"tg-{telegram_id}-{uuid.uuid4().hex[:6]}"
        payload: Dict[str, Any] = {
            "id": self.settings.inbound_id,
            "settings": {
                "clients": [
                    {
                        "id": uuid.uuid4().hex,
                        "email": remark,
                        "limitIp": 0,
                        "totalGB": traffic,
                        "expiryTime": expire,
                        "enable": True,
                        "flow": "xtls-rprx-vision",
                        "subId": uuid.uuid4().hex,
                        "tgId": str(telegram_id),
                    }
                ]
            },
            "remark": remark,
        }

        response = self.session.post(
            self._url("/panel/api/inbounds/addClient"), json=payload, timeout=20
        )
        if response.status_code != 200:
            raise VpnApiError(f"Failed to create user: {response.text}")

        data = response.json()
        client = data.get("obj") or data
        subscription = client.get("subscribeUrl") or client.get("url")
        qr_data = subscription or client.get("link")
        if not subscription:
            raise VpnApiError("Subscription URL missing in API response")

        return VpnUser(
            username=client.get("email", remark),
            remark=remark,
            subscription_url=subscription,
            qr_data=qr_data,
        )


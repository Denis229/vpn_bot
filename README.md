# Telegram VPN Bot

Python-бот, который принимает оплату через YooKassa и автоматически создаёт
VPN-профиль в панели [3x-ui](https://github.com/io-vpn/3x-ui). После оплаты
пользователь получает ссылку-подписку и QR-код для быстрой настройки.

## Быстрый старт
1. Установите зависимости:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Создайте файл `.env` c настройками:
   ```env
   TELEGRAM_TOKEN=123:token
   YOOKASSA_SHOP_ID=your_shop_id
   YOOKASSA_SECRET_KEY=your_secret
   PLAN_PRICE=299.0
   PANEL_BASE_URL=https://panel.example.com
   PANEL_API_KEY=your_panel_token
   INBOUND_ID=1
   DAYS_VALID=30
   TRAFFIC_GB=10
   STORAGE_PATH=data/payments.json
   BOT_NAME=My VPN Bot
   # опционально
   WEBHOOK_URL=https://your.domain/bot
   ```
3. Запустите бота:
   ```bash
   python -m bot.bot
   ```

## Как это работает
- `/start` выводит приветствие и кнопку оплаты.
- При нажатии «Оплатить» создаётся платёж в YooKassa и сохраняется в локальное хранилище.
- После успешной оплаты пользователь нажимает «Проверить оплату», бот проверяет
  статус платежа, создаёт клиента через API панели и отправляет ссылку-подписку
  и QR-код.

## Настройки API панели 3x-ui
- `PANEL_BASE_URL` — адрес панели (например, `https://panel.example.com`).
- `PANEL_API_KEY` — токен авторизации (используется в заголовке `Authorization: Bearer`).
- `INBOUND_ID` — идентификатор инбаунда, к которому добавляется клиент.
- `DAYS_VALID` и `TRAFFIC_GB` задают срок и трафик для созданной учётки.

## Файлы проекта
- `bot/bot.py` — Telegram-бот, обработчики команд и платежей.
- `bot/payments.py` — создание и проверка платежей в YooKassa.
- `bot/vpn_api.py` — клиент для панели 3x-ui.
- `bot/storage.py` — простое JSON-хранилище платежей.
- `bot/config.py` — модель настроек и вспомогательные классы.

## Предупреждения
- Хранилище платежей локальное и не предназначено для продакшена. Используйте
  внешнюю БД или кеш для распределённых инстансов.
- Для webhook-режима откройте порт и настройте HTTPS.

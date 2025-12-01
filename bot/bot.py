"""Telegram bot entry point."""
from __future__ import annotations

import io
import logging
import textwrap
from typing import Optional

import qrcode
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

from .config import VpnUser, get_settings
from .payments import YooKassaGateway
from .storage import PaymentRecord, PaymentStorage
from .vpn_api import VpnApiError, VpnPanelClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SETTINGS = get_settings()
PAYMENTS = PaymentStorage(SETTINGS.storage_path)
PANEL = VpnPanelClient(SETTINGS)
GATEWAY = YooKassaGateway(SETTINGS)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.effective_user
    text = textwrap.dedent(
        f"""
        Привет, {update.effective_user.first_name or 'друг'}! Я {SETTINGS.bot_name}.

        С моей помощью ты можешь оплатить доступ и получить персональную конфигурацию VPN.
        Стоимость подписки: <b>{SETTINGS.plan_price:.2f}₽</b> на {SETTINGS.days_valid} дней.

        Нажми кнопку ниже, чтобы перейти к оплате.
        """
    ).strip()
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton(text="Оплатить доступ", callback_data="buy")]]
    )
    await update.message.reply_html(text, reply_markup=keyboard)


async def buy_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    user = update.effective_user
    assert user

    description = f"VPN доступ для {user.id}"
    payment = GATEWAY.create_payment(
        description,
        metadata={
            "telegram_id": user.id,
            "return_url": SETTINGS.webhook_url or "https://t.me/" + SETTINGS.bot_name,
        },
    )

    record = PaymentRecord(
        payment_id=payment.id,
        telegram_id=user.id,
        amount=float(payment.amount.value),
        status=payment.status,
        confirmation_url=payment.confirmation.confirmation_url,
    )
    PAYMENTS.save(record)

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="Оплатить", url=payment.confirmation.confirmation_url
                )
            ],
            [
                InlineKeyboardButton(
                    text="Проверить оплату",
                    callback_data=f"check:{payment.id}",
                )
            ],
        ]
    )

    await query.edit_message_text(
        text=(
            "Перейди по ссылке для оплаты. После успешной оплаты нажми \"Проверить оплату\"."  # noqa: E501
        ),
        reply_markup=keyboard,
    )


async def check_payment(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data or ""
    payment_id: Optional[str] = None
    if data.startswith("check:"):
        payment_id = data.split(":", 1)[1]

    if not payment_id:
        await query.edit_message_text("Не удалось найти платеж. Попробуйте снова.")
        return

    record = PAYMENTS.get(payment_id)
    if not record:
        await query.edit_message_text("Платеж не найден в хранилище")
        return

    payment = GATEWAY.fetch_payment(payment_id)
    if payment.status != "succeeded":
        await query.edit_message_text(
            f"Статус платежа: {payment.status}. Повтори проверку после оплаты."
        )
        return

    PAYMENTS.update_status(payment_id, payment.status)

    try:
        vpn_user = PANEL.create_user(record.telegram_id)
    except VpnApiError as exc:
        logger.exception("Failed to create VPN user")
        await query.edit_message_text(
            f"Оплата прошла, но создать аккаунт не удалось: {exc}"
        )
        return

    await send_credentials(query, vpn_user)


async def send_credentials(query: Update, vpn_user: VpnUser) -> None:
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton(text="Подписка", url=vpn_user.subscription_url)]]
    )
    message = textwrap.dedent(
        f"""
        ✅ Доступ готов!

        Логин: <code>{vpn_user.username}</code>
        Подписка: <code>{vpn_user.subscription_url}</code>

        Добавь этот URI в клиент или отсканируй QR-код ниже.
        """
    ).strip()

    await query.edit_message_text(
        message, parse_mode=ParseMode.HTML, reply_markup=keyboard
    )

    qr_image = generate_qr(vpn_user.qr_data)
    await query.message.reply_photo(qr_image, caption="QR для быстрой настройки")


def generate_qr(data: str) -> io.BytesIO:
    img = qrcode.make(data)
    output = io.BytesIO()
    img.save(output, format="PNG")
    output.seek(0)
    return output


def build_app() -> Application:
    application = Application.builder().token(SETTINGS.telegram_token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(buy_handler, pattern="^buy$"))
    application.add_handler(CallbackQueryHandler(check_payment, pattern="^check:"))

    return application


def main() -> None:
    app = build_app()
    if SETTINGS.webhook_url:
        app.run_webhook(
            listen="0.0.0.0",
            port=8443,
            webhook_url=SETTINGS.webhook_url,
        )
    else:
        app.run_polling()


if __name__ == "__main__":
    main()


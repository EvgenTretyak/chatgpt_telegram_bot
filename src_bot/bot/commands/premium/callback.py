import json
from dataclasses import asdict
from typing import Dict

from telegram import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.constants import ParseMode
from telegram.ext import CallbackContext

from src_bot.bot.enums import CallbackQueryEnum
from src_bot.bot import messages
from src_bot.schemas.premium import Payment, PremiumTariff, payment_by_tariff
from src_bot.services.payment import stripe, yookassa


async def callback_query_premium_month_handle(
        update: Update,
        context: CallbackContext,
):
    # from bot.bot import register_user_if_not_exists
    #
    # await register_user_if_not_exists(
    #     update.callback_query,
    #     context,
    #     update.callback_query.from_user
    # )

    query: CallbackQuery = update.callback_query
    [_, month_tariff] = query.data.split('|')

    month_tariff = str(month_tariff)
    prices: Dict[str, Payment] = payment_by_tariff[month_tariff]

    reply_markup: InlineKeyboardMarkup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=str(prices["stripe"]),
                    callback_data=f'{CallbackQueryEnum.PAYMENT_CHOOSE}|{month_tariff}|stripe')
            ],
            [
                InlineKeyboardButton(
                    text=str(prices["yookassa"]),
                    callback_data=f'{CallbackQueryEnum.PAYMENT_CHOOSE}|{month_tariff}|yookassa')
            ],
            # [InlineKeyboardButton(f'💎 Crypto - {PRICES[query.data][0]}', callback_data=str(
            #     {"name": query.data, "type": "crypto", "amount": PRICES[query.data][0]}))],
        ],
    )
    await query.edit_message_reply_markup(reply_markup=reply_markup)


async def callback_query_payment_choose(
        update: Update,
        context: CallbackContext,
):
    query: CallbackQuery = update.callback_query

    [_, month_tariff, payment_type] = query.data.split('|')
    payment = payment_by_tariff[month_tariff][payment_type]

    await context.bot.send_message(chat_id=query.message.chat_id, text=str(payment))
    if payment.type == "stripe":
        payment_link = await stripe.process_payment(
            client_id=query.from_user.id,
            payment=payment,
        )
        # TODO - логика изменения статуса на премиум - вебхук на проверку статуса заявки
        await query.message.reply_text(
            text=messages.confirmation_payment_message,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(text='💳 Pay', url=payment_link)]]),
            parse_mode=ParseMode.HTML)
    elif payment.type == "yookassa":
        payment_link = await yookassa.process_payment(
            client_id=query.from_user.id,
            payment=payment,
        )
        await query.message.reply_text(
            text=messages.confirmation_payment_message,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(text='💳 Pay', url=payment_link)]]),
            parse_mode=ParseMode.HTML)
    else:
        reply_markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text='<<',
                        callback_data=f'{CallbackQueryEnum.PREMIUM_VIEW}',
                    ),
                ],
            ],
        )

        await query.answer()
        await update.callback_query.message.reply_text(
            text="",
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup,
        )
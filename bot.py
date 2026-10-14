#!/usr/bin/env python3
"""A bilingual Free Fire helper bot with manual diamond-order review."""

import json
import logging
import os
import re
import sys
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import store
import web_server
from shop_config import PAYMENT_METHODS, PRODUCT_BY_ID, PRODUCTS_BY_CATEGORY


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
)

LANGUAGE_MENU = {
    "keyboard": [
        [{"text": "🇷🇺 Русский"}],
        [{"text": "🇹🇯 Тоҷикӣ"}],
    ],
    "resize_keyboard": True,
    "is_persistent": True,
}

TRANSLATIONS = {
    "ru": {
        "buttons": {
            "news": "Новости игры",
            "stats": "Статистика игрока",
            "shop": "Купить",
            "ff_diamonds": "💎 Купить алмазы FF",
            "telegram_stars": "⭐ Купить Telegram Stars",
            "telegram_premium": "👑 Купить Telegram Premium",
            "diamonds": "Алмазы",
            "help": "Помощь",
            "back": "⬅️ Назад",
            "cancel": "Отмена",
            "confirm_uid": "✅ Да, UID верный",
            "change_uid": "✏️ Изменить UID",
            "ask_username": "Заказ №{order_id}. Введите ваш @username в Telegram (например: @username):",
            "invalid_username": "Неправильный формат. Введите @username, начинающийся с @.",
        },
        "package_labels": {
            "100": "💎 100 алмазов — 10 TJS",
            "300": "💎 300 алмазов — 29 TJS",
            "500": "💎 500 алмазов — 48 TJS",
            "1000": "💎 1 000 алмазов — 98 TJS",
            "weekly_voucher": "🎟 Недельный ваучер — 18 TJS",
            "monthly_voucher": "🎟 Месячный ваучер — 78 TJS",
            "stars_50": "⭐ 50 Telegram Stars — 15 TJS",
            "stars_100": "⭐ 100 Telegram Stars — 28 TJS",
            "stars_250": "⭐ 250 Telegram Stars — 65 TJS",
            "stars_500": "⭐ 500 Telegram Stars — 125 TJS",
            "premium_1_month": "👑 Telegram Premium — 1 месяц — 45 TJS",
            "premium_3_months": "👑 Telegram Premium — 3 месяца — 130 TJS",
            "premium_12_months": "👑 Telegram Premium — 12 месяцев — 400 TJS",
        },
        "product_names": {
            "100": "100 алмазов",
            "300": "300 алмазов",
            "500": "500 алмазов",
            "1000": "1 000 алмазов",
            "weekly_voucher": "Недельный ваучер",
            "monthly_voucher": "Месячный ваучер",
            "stars_50": "50 Telegram Stars",
            "stars_100": "100 Telegram Stars",
            "stars_250": "250 Telegram Stars",
            "stars_500": "500 Telegram Stars",
            "premium_1_month": "Telegram Premium — 1 месяц",
            "premium_3_months": "Telegram Premium — 3 месяца",
            "premium_12_months": "Telegram Premium — 12 месяцев",
        },
        "welcome": (
   "🎉 Добро пожаловать в ROYAL FF!\n\n"
            "💎 Мы продаём: алмазы Free Fire, Telegram Stars, Telegram Premium.\n\n"
"⚡ Быстро, надёжно, 24/7.\n\n"
"👇 Выберите раздел в меню ниже."
        ),
        "help": (
            "Выберите раздел в меню:\n"
            "• Новости игры — официальный сайт Free Fire.\n"
            "• Статистика игрока — просмотр статистики пока не подключён.\n"
            "• Купить — выберите товар, подтвердите UID и оплатите вручную.\n\n"
            "Отправьте /start, чтобы выбрать язык снова.\n"
            "Отправьте /id в личном чате, чтобы узнать свой Telegram ID."
        ),
        "news": (
            "У меня пока нет подключённой ленты новостей. "
            "Актуальные официальные новости Free Fire можно найти здесь:\n"
            "https://ff.garena.com/"
        ),
        "stats": (
            "Просмотр статистики игроков пока не подключён. "
            "Для этого нужен надёжный сервис статистики Free Fire."
        ),
        "unknown": "Выберите раздел с помощью кнопок в меню.",
        "choose_language": "Выберите язык / Забонро интихоб кунед:",
        "main_menu_return": "Главное меню.",
        "language_id": "Ваш Telegram ID: {user_id}",
        "id_private": "Отправьте /id в личном чате с ботом.",
        "only_private": (
            "Для покупки откройте личный чат с ботом. "
            "Так UID и чек не будут видны участникам группы."
        ),
        "choose_package": "Выберите товар:",
        "category_prompts": {
            "diamonds": "Выберите алмазы или ваучер:",
            "stars": "Выберите пакет Telegram Stars:",
            "premium": "Выберите срок Telegram Premium:",
        },
        "ask_uid": "Заказ №{order_id}. Введите ваш UID Free Fire (только цифры):",
        "invalid_uid": "UID должен содержать от 5 до 20 цифр. Попробуйте ещё раз.",
        "confirm_uid": "Проверьте UID: {uid}\nЭто ваш UID?",
        "uid_changed": "Введите UID Free Fire ещё раз цифрами.",
        "order_summary": (
            "Проверьте заказ №{order_id}:\n"
            "Товар: {product_name}\n"
            "Цена: {price} TJS\n"
            "UID Free Fire: {uid}\n\n"
            "Если всё верно, выберите способ оплаты ниже."
        ),
        "choose_payment": "Выберите способ оплаты:",
        "payment_instructions": (
            "Заказ №{order_id}\n"
            "Товар: {product_name}\n"
            "UID Free Fire: {uid}\n"
            "Сумма: {price} TJS\n"
            "Способ оплаты: {method}\n\n"
            "Данные для оплаты:\n{details}\n\n"
            "После перевода отправьте сюда фото чека. "
            "Фото чека само по себе не подтверждает оплату."
        ),
        "receipt_prompt": (
            "Отправьте фото чека об оплате в этот чат. "
            "Заказ будет ждать ручной проверки администратора."
        ),
        "receipt_received": (
            "Фото чека получено. Оплата ещё не подтверждена. "
            "Администратор проверит перевод вручную."
        ),
        "receipt_retry": (
            "Это фото уже отправлялось, но не было передано на проверку. "
            "Пожалуйста, отправьте фото чека ещё раз как новое сообщение."
        ),
        "receipt_delivery_failed": (
            "Не удалось передать чек администратору. "
            "Отправьте фото чека ещё раз. Оплата не подтверждена."
        ),
        "no_order_for_receipt": (
            "Сначала выберите категорию товара, товар и способ оплаты. "
            "Затем отправьте фото чека."
        ),
        "finish_order_first": (
            "Сначала завершите текущий шаг заказа. "
            "Подтвердите UID или выберите способ оплаты в меню."
        ),
        "existing_receipt_order": (
            "У вас уже есть незавершённый заказ №{order_id}. "
            "Завершите его, прежде чем начинать новый заказ."
        ),
        "cancelled": "Черновик заказа отменён. Оплата не подтверждена.",
        "order_expired": (
            "Заказ №{order_id} автоматически отменён через 20 минут без чека. "
            "Если вы уже оплатили, свяжитесь с администратором."
        ),
        "cannot_cancel_after_payment": (
            "Заказ №{order_id} уже ожидает чек. Если вы перевели деньги, "
            "отправьте чек для проверки. Не оплачивайте второй раз."
        ),
        "no_active_order": "Сейчас нет незавершённого заказа.",
        "admin_caption": (
            "Заказ №{order_id}\n"
            "Сумма: {price} TJS\n"
            "Товар: {product_name}\n"
            "Free Fire UID: {uid}\n"
            "Способ оплаты: {method}\n\n"
            "Проверьте поступление вручную. Фото чека не подтверждает оплату."
        ),
        "approve_button": "Одобрить оплату",
        "reject_button": "Отклонить оплату",
        "admin_only": "Эти кнопки доступны только администратору.",
        "order_not_pending": "Заказ уже проверен или кнопка недействительна.",
        "approved_admin": "Оплата одобрена. Заказ передан в обработку.",
        "rejected_admin": "Оплата отклонена.",
        "approved_customer": (
            "Оплата по заказу №{order_id} проверена и одобрена. "
            "Заказ передан в обработку. Товар ещё не доставлен."
        ),
        "rejected_customer": (
            "Оплата по заказу №{order_id} не подтверждена. "
            "Свяжитесь с администратором, если вы уже перевели деньги."
        ),
        "cancel_label": "Отмена",
    },
  "tg": {
        "buttons": {
            "news": "Хабарҳои бозӣ",
            "stats": "Омори бозигар",
            "shop": "Харид",
            "ff_diamonds": "💎 Харидани алмосҳои FF",
            "telegram_stars": "⭐ Харидани Telegram Stars",
            "telegram_premium": "👑 Харидани Telegram Premium",
            "diamonds": "Алмосҳо",
            "help": "Кӯмак",
            "back": "⬅️ Бозгашт",
            "cancel": "Бекор кардан",
            "confirm_uid": "✅ Бале, UID дуруст аст",
            "change_uid": "✏️ UID-ро иваз кардан",
            "ask_username": "Фармоиш №{order_id}. @username-и худро дар Telegram нависед (мисол: @username):",
            "invalid_username": "Формати нодуруст. @username-ро бо аломати @ нависед.",
        },
        "package_labels": {
            "100": "💎 100 алмос — 10 TJS",
            "300": "💎 300 алмос — 29 TJS",
            "500": "💎 500 алмос — 48 TJS",
            "1000": "💎 1 000 алмос — 98 TJS",
            "weekly_voucher": "🎟 Ваучери ҳафтаина — 18 TJS",
            "monthly_voucher": "🎟 Ваучери моҳона — 78 TJS",
            "stars_50": "⭐ 50 Telegram Stars — 15 TJS",
            "stars_100": "⭐ 100 Telegram Stars — 28 TJS",
            "stars_250": "⭐ 250 Telegram Stars — 65 TJS",
            "stars_500": "⭐ 500 Telegram Stars — 125 TJS",
            "premium_1_month": "👑 Telegram Premium — 1 моҳ — 45 TJS",
            "premium_3_months": "👑 Telegram Premium — 3 моҳ — 130 TJS",
            "premium_12_months": "👑 Telegram Premium — 12 моҳ — 400 TJS",
        },
        "product_names": {
            "100": "100 алмос",
            "300": "300 алмос",
            "500": "500 алмос",
            "1000": "1 000 алмос",
            "weekly_voucher": "Ваучери ҳафтаина",
            "monthly_voucher": "Ваучери моҳона",
            "stars_50": "50 Telegram Stars",
            "stars_100": "100 Telegram Stars",
            "stars_250": "250 Telegram Stars",
            "stars_500": "500 Telegram Stars",
            "premium_1_month": "Telegram Premium — 1 моҳ",
            "premium_3_months": "Telegram Premium — 3 моҳ",
            "premium_12_months": "Telegram Premium — 12 моҳ",
        },
        "welcome": (
            "🎉 Хуш омадед ба ROYAL FF!\n\n"
            "💎 Мо мефурӯшем: алмосҳои Free Fire ва Telegram Stars.\n\n"
            "⚡ Зуд ва боэътимод.\n\n"
            "👇 Аз меню интихоб кунед."
),
        "help": (
            "Аз меню бахшеро интихоб кунед:\n"
            "• Хабарҳои бозӣ — сомонаи расмии Free Fire.\n"
            "• Омори бозигар — дидани омор ҳоло пайваст нест.\n"
            "• Харид — молро интихоб кунед, UID-ро тасдиқ карда, пардохт намоед.\n\n"
            "Барои аз нав интихоб кардани забон /start-ро фиристед.\n"
            "Барои дидани ID-и Telegram дар чати шахсӣ /id-ро фиристед."
        ),
        "news": (
            "Ман ҳоло ба бахши хабарҳо пайваст нестам. "
            "Хабарҳои расмии Free Fire-ро дар ин сомона бинед:\n"
            "https://ff.garena.com/"
        ),
        "stats": (
            "Омори бозигарон ҳоло пайваст нест. "
            "Барои ин хусусият манбаи боэътимоди омори Free Fire лозим аст."
        ),
        "unknown": "Аз тугмаҳои меню як бахшро интихоб кунед.",
        "choose_language": "Выберите язык / Забонро интихоб кунед:",
        "main_menu_return": "Менюи асосӣ.",
        "language_id": "ID-и Telegram-и шумо: {user_id}",
        "id_private": "Лутфан, /id-ро дар чати шахсӣ бо бот фиристед.",
        "only_private": (
            "Барои харид чати шахсиро бо бот кушоед. "
            "Ҳамин тавр UID ва чекро иштирокчиёни гурӯҳ намебинанд."
        ),
        "choose_package": "Молро интихоб кунед:",
        "category_prompts": {
            "diamonds": "Алмос ё ваучерро интихоб кунед:",
            "stars": "Бастаи Telegram Stars-ро интихоб кунед:",
            "premium": "Муҳлати Telegram Premium-ро интихоб кунед:",
        },
        "ask_uid": "Фармоиш №{order_id}. UID-и Free Fire-ро ворид кунед (танҳо рақамҳо):",
        "invalid_uid": "UID бояд аз 5 то 20 рақам бошад. Бори дигар кӯшиш кунед.",
        "confirm_uid": "UID-ро санҷед: {uid}\nИн UID-и шумост?",
        "uid_changed": "UID-и Free Fire-ро бо рақам аз нав ворид кунед.",
        "order_summary": (
            "Фармоиши №{order_id}-ро санҷед:\n"
            "Мол: {product_name}\n"
            "Нарх: {price} TJS\n"
            "UID-и Free Fire: {uid}\n\n"
            "Агар ҳамааш дуруст бошад, усули пардохтро аз меню интихоб кунед."
        ),
        "choose_payment": "Усули пардохтро интихоб кунед:",
        "payment_instructions": (
            "Фармоиш №{order_id}\n"
            "Мол: {product_name}\n"
            "UID-и Free Fire: {uid}\n"
            "Маблағ: {price} TJS\n"
            "Усули пардохт: {method}\n\n"
            "Маълумоти пардохт:\n{details}\n\n"
            "Пас аз пардохт акси чекро ба ҳамин чат фиристед. "
            "Акси чек худ аз худ пардохтро тасдиқ намекунад."
        ),
        "receipt_prompt": (
            "Акси чеки пардохтро ба ҳамин чат фиристед. "
            "Маъмур фармоишро дастӣ месанҷад."
        ),
        "receipt_received": (
            "Акси чек қабул шуд. Пардохт ҳанӯз тасдиқ нашудааст. "
            "Маъмур маблағро дастӣ месанҷад."
        ),
        "receipt_retry": (
            "Ин акс аллакай фиристода шуда буд, вале ба маъмур нарасидааст. "
            "Лутфан, акси чекро ҳамчун паёми нав дубора фиристед."
        ),
        "receipt_delivery_failed": (
            "Чекро ба маъмур фиристода натавонистам. "
            "Акси чекро дубора фиристед. Пардохт тасдиқ нашудааст."
        ),
        "no_order_for_receipt": (
            "Аввал гурӯҳи мол, мол ва усули пардохтро интихоб кунед. "
            "Баъд акси чекро фиристед."
        ),
        "finish_order_first": (
            "Аввал қадами ҷории фармоишро анҷом диҳед. "
            "UID-ро тасдиқ кунед ё усули пардохтро интихоб кунед."
        ),
        "existing_receipt_order": (
            "Шумо аллакай фармоиши нотамоми №{order_id} доред. "
            "Пеш аз фармоиши нав онро анҷом диҳед."
        ),
        "cancelled": "Қисми нотамоми фармоиш бекор шуд. Пардохт тасдиқ нашудааст.",
        "order_expired": (
            "Фармоиши №{order_id} пас аз 20 дақиқа бе чек худкор бекор шуд. "
            "Агар аллакай пардохт карда бошед, бо маъмур тамос гиред."
        ),
        "cannot_cancel_after_payment": (
            "Фармоиши №{order_id} чекро интизор аст. Агар пул фиристодед, "
            "чекро барои санҷиш фиристед. Дубора пул нафиристед."
        ),
        "no_active_order": "Ҳоло фармоиши нотамом надоред.",
        "admin_caption": (
            "Фармоиш №{order_id}\n"
            "Маблағ: {price} TJS\n"
            "Мол: {product_name}\n"
            "UID-и Free Fire: {uid}\n"
            "Усули пардохт: {method}\n\n"
            "Ворид шудани маблағро дастӣ санҷед. Акси чек пардохтро тасдиқ намекунад."
        ),
        "approve_button": "Тасдиқи пардохт",
        "reject_button": "Рад кардани пардохт",
        "admin_only": "Ин тугмаҳо танҳо барои маъмур ҳастанд.",
        "order_not_pending": "Фармоиш аллакай санҷида шудааст ё тугма дигар амал намекунад.",
        "approved_admin": "Пардохт тасдиқ шуд. Фармоиш ба иҷро фиристода шуд.",
        "rejected_admin": "Пардохт рад карда шуд.",
        "approved_customer": (
            "Пардохти фармоиши №{order_id} санҷида ва тасдиқ шуд. "
            "Фармоиш ба иҷро фиристода шуд. Мол ҳанӯз расонида нашудааст."
        ),
        "rejected_customer": (
            "Пардохти фармоиши №{order_id} тасдиқ нашуд. "
            "Агар пул фиристода бошед, бо маъмур тамос гиред."
        ),
        "cancel_label": "Бекор кардан",
    },
}

LANGUAGE_BUTTONS = {
    "🇷🇺 русский": "ru",
    "🇹🇯 тоҷикӣ": "tg",
}

BUTTON_ACTIONS = {
    "game news": "news",
    "новости игры": "news",
    "хабарҳои бозӣ": "news",
    "player stats": "stats",
    "статистика игрока": "stats",
    "омори бозигар": "stats",
    "help": "help",
    "помощь": "help",
    "кӯмак": "help",
    "shop": "shop_diamonds",
    "купить": "shop_diamonds",
    "харид": "shop_diamonds",
    "магазин": "shop_diamonds",
    "дӯкон": "shop_diamonds",
    "мағоза": "shop_diamonds",
    "diamonds": "shop_diamonds",
    "алмазы": "shop_diamonds",
    "алмосҳо": "shop_diamonds",
    "💎 купить алмазы ff": "shop_diamonds",
    "💎 харидани алмосҳои ff": "shop_diamonds",
    "⭐ купить telegram stars": "shop_stars",
    "⭐ харидани telegram stars": "shop_stars",
    "👑 купить telegram premium": "shop_premium",
    "👑 харидани telegram premium": "shop_premium",
}

SHOP_CATEGORY_BY_ACTION = {
    "shop_diamonds": "diamonds",
    "shop_stars": "stars",
    "shop_premium": "premium",
}

PACKAGE_LABEL_TO_ID = {
    label.casefold(): package_id
    for language in TRANSLATIONS.values()
    for package_id, label in language["package_labels"].items()
}

PAYMENT_METHOD_BUTTONS = {
    "alif": "alif",
    "dushanbe city": "dushanbe_city",
}

CANCEL_BUTTONS = {
    TRANSLATIONS["ru"]["buttons"]["cancel"].casefold(),
    TRANSLATIONS["tg"]["buttons"]["cancel"].casefold(),
}
BACK_BUTTONS = {
    TRANSLATIONS["ru"]["buttons"]["back"].casefold(),
    TRANSLATIONS["tg"]["buttons"]["back"].casefold(),
}
UID_CONFIRM_BUTTONS = {
    TRANSLATIONS["ru"]["buttons"]["confirm_uid"].casefold(),
    TRANSLATIONS["tg"]["buttons"]["confirm_uid"].casefold(),
}
UID_CHANGE_BUTTONS = {
    TRANSLATIONS["ru"]["buttons"]["change_uid"].casefold(),
    TRANSLATIONS["tg"]["buttons"]["change_uid"].casefold(),
}


class TelegramAPIError(Exception):
    """An API error that deliberately never includes the token or request URL."""

    def __init__(self, status_code: int | None = None) -> None:
        super().__init__("Telegram API request failed")
        self.status_code = status_code


def telegram_call(token: str, method: str, data: dict[str, Any]) -> Any:
    """Call Telegram's Bot API without printing or exposing the bot token."""
    url = f"https://api.telegram.org/bot{token}/{method}"
    body = json.dumps(data).encode("utf-8")
    request = Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=35) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        raise TelegramAPIError(error.code) from None
    except (URLError, TimeoutError, OSError):
        raise TelegramAPIError() from None
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise TelegramAPIError() from None

    if not result.get("ok"):
        raise TelegramAPIError(result.get("error_code"))
    return result.get("result")


def send_message(
    token: str,
    chat_id: int,
    text: str,
    reply_markup: dict[str, Any] | None = None,
) -> Any:
    payload: dict[str, Any] = {"chat_id": chat_id, "text": text}
    if reply_markup is not None:
        payload["reply_markup"] = reply_markup
    result = telegram_call(token, "sendMessage", payload)
    menu_context = menu_context_for_markup(reply_markup)
    if menu_context:
        store.save_chat_menu_context(chat_id, menu_context)
    return result


def menu_context_for_markup(
    reply_markup: dict[str, Any] | None,
) -> str | None:
    if not reply_markup:
        return None
    keyboard = reply_markup.get("keyboard")
    if not isinstance(keyboard, list):
        return None
    labels = {
        str(button.get("text", "")).casefold()
        for row in keyboard
        for button in row
        if isinstance(button, dict)
    }
    if labels.intersection(LANGUAGE_BUTTONS):
        return "language"

    if any(
        {
            TRANSLATIONS[language]["buttons"][key].casefold()
            for key in ("ff_diamonds", "telegram_stars", "telegram_premium")
        }.issubset(labels)
        for language in TRANSLATIONS
    ):
        return "main"

    product_labels = {
        label.casefold()
        for language in TRANSLATIONS.values()
        for label in language["package_labels"].values()
    }
    if labels.intersection(product_labels):
        return "shop"
    return None


def main_menu(language: str) -> dict[str, Any]:
    buttons = TRANSLATIONS[language]["buttons"]
    return {
        "keyboard": [
            [{"text": buttons["ff_diamonds"]}],
            [{"text": buttons["telegram_stars"]}],
            [{"text": buttons["telegram_premium"]}],
            [{"text": buttons["back"]}],
        ],
        "resize_keyboard": True,
        "is_persistent": True,
    }


def package_menu(language: str, category: str = "diamonds") -> dict[str, Any]:
    messages = TRANSLATIONS[language]
    labels = messages["package_labels"]
    keyboard = []
    products = PRODUCTS_BY_CATEGORY[category]
    for index in range(0, len(products), 2):
        keyboard.append(
            [
                {"text": labels[product["id"]]}
                for product in products[index : index + 2]
            ]
        )
    keyboard.append([{"text": messages["buttons"]["back"]}])
    return {
        "keyboard": keyboard,
        "resize_keyboard": True,
        "is_persistent": True,
    }


def payment_menu(language: str) -> dict[str, Any]:
    messages = TRANSLATIONS[language]
    return {
        "keyboard": [
            [{"text": PAYMENT_METHODS["alif"]}],
            [{"text": PAYMENT_METHODS["dushanbe_city"]}],
            [{"text": messages["buttons"]["cancel"]}],
        ],
        "resize_keyboard": True,
        "is_persistent": True,
    }


def uid_prompt_menu(language: str) -> dict[str, Any]:
    return {
        "keyboard": [[{"text": TRANSLATIONS[language]["buttons"]["cancel"]}]],
        "resize_keyboard": True,
        "is_persistent": True,
    }

 def username_prompt_menu(language: str) -> dict[str, Any]:
    return {
        "keyboard": [[{"text": TRANSLATIONS[language]["buttons"]["cancel"]}]],
        "resize_keyboard": True,
        "is_persistent": True,
    }

def uid_confirmation_menu(language: str) -> dict[str, Any]:
    buttons = TRANSLATIONS[language]["buttons"]
    return {
        "keyboard": [
            [{"text": buttons["confirm_uid"]}],
            [{"text": buttons["change_uid"]}],
            [{"text": buttons["cancel"]}],
        ],
        "resize_keyboard": True,
        "is_persistent": True,
    }


def receipt_review_buttons(order_id: int, language: str) -> dict[str, Any]:
    messages = TRANSLATIONS[language]
    return {
        "inline_keyboard": [
            [
                {
                    "text": messages["approve_button"],
                    "callback_data": f"ffh:approve:{order_id}",
                },
                {
                    "text": messages["reject_button"],
                    "callback_data": f"ffh:reject:{order_id}",
                },
            ]
        ]
    }


def package_id_for_button(button: str) -> str | None:
    return PACKAGE_LABEL_TO_ID.get(button.casefold())


def price_for_display(price_tjs: str) -> str:
    return price_tjs.replace(".", ",")


def product_name(language: str, product_id: str) -> str:
    messages = TRANSLATIONS[language]
    return messages["product_names"].get(product_id, product_id)


def is_receipt_photo(message: dict[str, Any]) -> bool:
    if message.get("photo"):
        return True
    document = message.get("document") or {}
    return bool((document.get("mime_type") or "").startswith("image/"))


def load_configuration() -> tuple[str, int, dict[str, str]] | None:
    required = {
        "TELEGRAM_BOT_TOKEN": os.environ.get("TELEGRAM_BOT_TOKEN", "").strip(),
        "ADMIN_TELEGRAM_ID": os.environ.get("ADMIN_TELEGRAM_ID", "").strip(),
        "ALIF_PAYMENT_DETAILS": os.environ.get("ALIF_PAYMENT_DETAILS", "").strip(),
        "DUSHANBE_CITY_PAYMENT_DETAILS": os.environ.get(
            "DUSHANBE_CITY_PAYMENT_DETAILS", ""
        ).strip(),
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        logging.error(
            "Add these missing values in Replit Secrets: %s",
            ", ".join(missing),
        )
        return None

    if not re.fullmatch(r"[0-9]+", required["ADMIN_TELEGRAM_ID"]):
        logging.error(
            "ADMIN_TELEGRAM_ID must be a numeric Telegram user ID. "
            "Use /id in a private bot chat."
        )
        return None

    admin_id = int(required["ADMIN_TELEGRAM_ID"])
    if admin_id <= 0:
        logging.error("ADMIN_TELEGRAM_ID must be greater than zero.")
        return None

    if (
        len(required["ALIF_PAYMENT_DETAILS"]) > 2000
        or len(required["DUSHANBE_CITY_PAYMENT_DETAILS"]) > 2000
    ):
        logging.error(
            "Payment instructions are too long. Keep each payment detail under 2,000 characters."
        )
        return None

    return (
        required["TELEGRAM_BOT_TOKEN"],
        admin_id,
        {
            "alif": required["ALIF_PAYMENT_DETAILS"],
            "dushanbe_city": required["DUSHANBE_CITY_PAYMENT_DETAILS"],
        },
    )


def send_language_prompt(token: str, chat_id: int) -> None:
    send_message(
        token,
        chat_id,
        "Выберите язык / Забонро интихоб кунед:",
        LANGUAGE_MENU,
    )


def send_package_list(
    token: str,
    chat_id: int,
    language: str,
    category: str = "diamonds",
) -> None:
    send_message(
        token,
        chat_id,
        TRANSLATIONS[language]["category_prompts"][category],
        package_menu(language, category),
    )


def send_order_payment_instructions(
    token: str,
    chat_id: int,
    language: str,
    order: dict[str, Any],
    payment_details: dict[str, str],
) -> None:
    messages = TRANSLATIONS[language]
    method = PAYMENT_METHODS[order["payment_method"]]
    answer = messages["payment_instructions"].format(
        order_id=order["order_id"],
        product_name=product_name(language, order["package_id"]),
        uid=order["free_fire_uid"],
        price=price_for_display(order["price_tjs"]),
        method=method,
        details=payment_details[order["payment_method"]],
    )
    send_message(token, chat_id, answer, main_menu(language))


def send_order_summary(
    token: str,
    chat_id: int,
    language: str,
    order: dict[str, Any],
) -> None:
    messages = TRANSLATIONS[language]
    answer = messages["order_summary"].format(
        order_id=order["order_id"],
        product_name=product_name(language, order["package_id"]),
        price=price_for_display(order["price_tjs"]),
        uid=order["free_fire_uid"],
    )
    send_message(token, chat_id, answer, payment_menu(language))


def send_receipt_to_admin(
    token: str,
    admin_id: int,
    order: dict[str, Any],
) -> int:
    admin_language = store.get_user_language(admin_id) or "ru"
    admin_language = admin_language if admin_language in TRANSLATIONS else "ru"
    messages = TRANSLATIONS[admin_language]
    caption = messages["admin_caption"].format(
        order_id=order["order_id"],
        price=price_for_display(order["price_tjs"]),
        product_name=product_name(admin_language, order["package_id"]),
        uid=order["free_fire_uid"],
        method=PAYMENT_METHODS[order["payment_method"]],
    )
    result = telegram_call(
        token,
        "copyMessage",
        {
            "chat_id": admin_id,
            "from_chat_id": order["receipt_chat_id"],
            "message_id": order["receipt_message_id"],
            "caption": caption,
            "reply_markup": receipt_review_buttons(order["order_id"], admin_language),
        },
    )
    message_id = result.get("message_id") if isinstance(result, dict) else None
    if not message_id:
        raise TelegramAPIError()
        return int(message_id)


def send_receipt_to_second_admin(
    token: str,
    order: dict[str, Any],
) -> None:
    second_admin_id_raw = os.environ.get("SECOND_ADMIN_TELEGRAM_ID", "").strip()
    if not second_admin_id_raw or not second_admin_id_raw.isdigit():
        return
    admin_id = int(second_admin_id_raw)
    admin_language = store.get_user_language(admin_id) or "ru"
    admin_language = admin_language if admin_language in TRANSLATIONS else "ru"
    messages = TRANSLATIONS[admin_language]
    caption = messages["admin_caption"].format(
        order_id=order["order_id"],
        price=price_for_display(order["price_tjs"]),
        product_name=product_name(admin_language, order["package_id"]),
        uid=order["free_fire_uid"],
        method=PAYMENT_METHODS[order["payment_method"]],
    )
    try:
        telegram_call(
            token,
            "copyMessage",
            {
                "chat_id": admin_id,
                "from_chat_id": order["receipt_chat_id"],
                "message_id": order["receipt_message_id"],
                "caption": caption,
                "reply_markup": receipt_review_buttons(order["order_id"], admin_language),
            },
        )
    except TelegramAPIError:
        logging.warning("Could not send receipt to second admin %s.", admin_id)


def process_receipt_photo(
    token: str,
    admin_id: int,
    user_id: int,
    chat_id: int,
    language: str,
    order: dict[str, Any],
    message: dict[str, Any],
) -> None:
    source_message_id = message.get("message_id")
    if not source_message_id:
        send_message(
            token,
            chat_id,
            TRANSLATIONS[language]["receipt_delivery_failed"],
            main_menu(language),
        )
        return

    if (
        order.get("receipt_chat_id") == chat_id
        and order.get("receipt_message_id") == source_message_id
    ):
        send_message(
            token,
            chat_id,
            TRANSLATIONS[language]["receipt_retry"],
            main_menu(language),
        )
        return

    if not store.begin_receipt_delivery(
        order["order_id"],
        user_id,
        chat_id,
        source_message_id,
    ):
        send_message(
            token,
            chat_id,
            TRANSLATIONS[language]["receipt_retry"],
            main_menu(language),
        )
        return

    order_for_admin = store.get_order(order["order_id"])
    if not order_for_admin:
        raise RuntimeError("Order disappeared while preparing receipt review")

    try:
        admin_message_id = send_receipt_to_admin(token, admin_id, order_for_admin)
        send_receipt_to_second_admin(token, order_for_admin)
    except TelegramAPIError:
        store.restore_receipt_waiting(order["order_id"])
        send_message(
            token,
            chat_id,
            TRANSLATIONS[language]["receipt_delivery_failed"],
            main_menu(language),
        )
        return

    if not store.mark_receipt_pending_review(
        order["order_id"],
        admin_message_id,
    ):
        store.restore_receipt_waiting(order["order_id"])
        send_message(
            token,
            chat_id,
            TRANSLATIONS[language]["receipt_delivery_failed"],
            main_menu(language),
        )
        return

    send_message(
        token,
        chat_id,
        TRANSLATIONS[language]["receipt_received"],
        main_menu(language),
    )


def process_message(
    token: str,
    admin_id: int,
    payment_details: dict[str, str],
    message: dict[str, Any],
) -> None:
    chat = message.get("chat") or {}
    sender = message.get("from") or {}
    chat_id = chat.get("id")
    user_id = sender.get("id")
    text = (message.get("text") or "").strip()
    chat_type = chat.get("type", "private")

    if not chat_id or not user_id:
        return

    command = text.split(maxsplit=1)[0].split("@", maxsplit=1)[0].lower() if text else ""
    button = text.casefold()

    if command == "/start":
        send_language_prompt(token, chat_id)
        return

    selected_language = LANGUAGE_BUTTONS.get(button)
    if selected_language:
        store.save_user_language(user_id, selected_language)
        send_message(
            token,
            chat_id,
            TRANSLATIONS[selected_language]["welcome"],
            main_menu(selected_language),
        )
        return

    language = store.get_user_language(user_id)
    if language not in TRANSLATIONS:
        send_language_prompt(token, chat_id)
        return

    messages = TRANSLATIONS[language]

    if command == "/id":
        if chat_type != "private":
            send_message(token, chat_id, messages["id_private"])
        else:
            send_message(
                token,
                chat_id,
                messages["language_id"].format(user_id=user_id),
            )
        return

    if command == "/help" or button in {"help", "помощь", "кӯмак"}:
        send_message(token, chat_id, messages["help"], main_menu(language))
        return

    action = BUTTON_ACTIONS.get(button)
    if action in {"news", "stats"}:
        send_message(token, chat_id, messages[action], main_menu(language))
        return

    if is_receipt_photo(message):
        if chat_type != "private":
            send_message(token, chat_id, messages["only_private"])
            return
        order = store.get_active_order(user_id)
        if not order:
            send_message(token, chat_id, messages["no_order_for_receipt"], main_menu(language))
        elif order["status"] == "awaiting_receipt" and order["payment_method"]:
            process_receipt_photo(
                token,
                admin_id,
                user_id,
                chat_id,
                language,
                order,
                message,
            )
        elif order["status"] == "awaiting_receipt":
            send_order_summary(token, chat_id, language, order)
        else:
            send_message(token, chat_id, messages["finish_order_first"])
        return

    if command == "/cancel" or button in CANCEL_BUTTONS:
        order = store.get_active_order(user_id)
        if not order:
            send_message(token, chat_id, messages["no_active_order"], main_menu(language))
        elif order["status"] == "awaiting_receipt" and order["payment_method"]:
            send_message(
                token,
                chat_id,
                messages["cannot_cancel_after_payment"].format(
                    order_id=order["order_id"]
                ),
                main_menu(language),
            )
        else:
            store.cancel_draft_order(order["order_id"], user_id)
            send_message(token, chat_id, messages["cancelled"], main_menu(language))
        return

    if button in BACK_BUTTONS:
        if store.get_chat_menu_context(chat_id) == "shop":
            send_message(
                token,
                chat_id,
                messages["main_menu_return"],
                main_menu(language),
            )
        else:
            send_language_prompt(token, chat_id)
        return

    if action in SHOP_CATEGORY_BY_ACTION:
        if chat_type != "private":
            send_message(token, chat_id, messages["only_private"])
            return
        order = store.get_active_order(user_id)
        if order and order["status"] == "awaiting_receipt" and order["payment_method"]:
            send_message(
                token,
                chat_id,
                messages["existing_receipt_order"].format(
                    order_id=order["order_id"]
                ),
                main_menu(language),
            )
        elif order and order["status"] == "awaiting_receipt":
            send_order_summary(token, chat_id, language, order)
        elif order and order["status"] == "awaiting_payment_method":
            send_message(
                token,
                chat_id,
                messages["confirm_uid"].format(uid=order["free_fire_uid"]),
                uid_confirmation_menu(language),
            )
        elif order and order["status"] == "awaiting_uid":
            send_message(
                token,
                chat_id,
                messages["ask_uid"].format(order_id=order["order_id"]),
                uid_prompt_menu(language),
            )
        else:
            send_package_list(
                token,
                chat_id,
                language,
                SHOP_CATEGORY_BY_ACTION[action],
            )
        return

    selected_package_id = package_id_for_button(button)
    if selected_package_id:
        if chat_type != "private":
            send_message(token, chat_id, messages["only_private"])
            return
        order = store.get_active_order(user_id)
        if order and order["status"] == "awaiting_receipt" and order["payment_method"]:
            send_message(
                token,
                chat_id,
                messages["existing_receipt_order"].format(
                    order_id=order["order_id"]
                ),
                main_menu(language),
            )
            return
        if order and order["status"] == "awaiting_receipt":
            send_order_summary(token, chat_id, language, order)
            return
        if order:
            store.cancel_draft_order(order["order_id"], user_id)
        package = PRODUCT_BY_ID[selected_package_id]
category = package.get("category", "diamonds")

if category == "diamonds":
    order = store.create_order(
        user_id=user_id,
        chat_id=chat_id,
        language=language,
        package_id=package["id"],
        diamonds=package["diamonds"],
        price_tjs=package["price_tjs"],
    )
    send_message(
        token,
        chat_id,
        messages["ask_uid"].format(order_id=order["order_id"]),
        uid_prompt_menu(language),
    )
else:
    order = store.create_order(
        user_id=user_id,
        chat_id=chat_id,
        language=language,
        package_id=package["id"],
        diamonds=package["diamonds"],
        price_tjs=package["price_tjs"],
        initial_status="awaiting_receipt",
    )
    send_message(
        token,
        chat_id,
        messages["ask_username"].format(order_id=order["order_id"]),
        username_prompt_menu(language),
    )
return

    if button in UID_CONFIRM_BUTTONS or button in UID_CHANGE_BUTTONS:
        order = store.get_active_order(user_id)
        if not order or order["status"] != "awaiting_payment_method":
            send_message(token, chat_id, messages["unknown"], main_menu(language))
            return
        if button in UID_CHANGE_BUTTONS:
            if store.reset_free_fire_uid(order["order_id"], user_id):
                send_message(
                    token,
                    chat_id,
                    messages["uid_changed"],
                    uid_prompt_menu(language),
                )
            return
        if store.confirm_free_fire_uid(order["order_id"], user_id):
            confirmed_order = store.get_order(order["order_id"])
            if confirmed_order:
                send_order_summary(token, chat_id, language, confirmed_order)
        return

    if button == "alif":
        selected_method = "alif"
    elif button == "dushanbe city":
        selected_method = "dushanbe_city"
    else:
        selected_method = None

    if selected_method:
        if chat_type != "private":
            send_message(token, chat_id, messages["only_private"])
            return
        order = store.get_active_order(user_id)
        if (
            not order
            or order["status"] != "awaiting_receipt"
            or order["payment_method"] is not None
        ):
            send_message(token, chat_id, messages["unknown"], main_menu(language))
            return
        if store.save_payment_method(
            order["order_id"],
            user_id,
            selected_method,
        ):
            order = store.get_order(order["order_id"])
            if order:
                send_order_payment_instructions(
                    token,
                    chat_id,
                    language,
                    order,
                    payment_details,
                )
        return

    order = store.get_active_order(user_id)
    if not order:
        send_message(token, chat_id, messages["unknown"], main_menu(language))
        return

    if chat_type != "private":
        send_message(token, chat_id, messages["only_private"])
        return

    if order["status"] == "awaiting_uid":
        if not re.fullmatch(r"[0-9]{5,20}", text):
            send_message(
                token,
                chat_id,
                messages["invalid_uid"],
                uid_prompt_menu(language),
            )
            return
        if store.save_free_fire_uid(order["order_id"], user_id, text):
            send_message(
                token,
                chat_id,
                messages["confirm_uid"].format(uid=text),
                uid_confirmation_menu(language),
            )
        return
        if order["status"] == "awaiting_receipt" and order["free_fire_uid"] is None and order["payment_method"] is None:
    if not re.fullmatch(r"@[A-Za-z0-9_]{4,32}", text):
        send_message(
            token,
            chat_id,
            messages["invalid_username"],
            username_prompt_menu(language),
        )
        return
    store.save_free_fire_uid(order["order_id"], user_id, text)
    updated_order = store.get_order(order["order_id"])
    if updated_order:
        send_order_summary(token, chat_id, language, updated_order)
    return

    if order["status"] == "awaiting_payment_method":
        send_message(
            token,
            chat_id,
            messages["confirm_uid"].format(uid=order["free_fire_uid"]),
            uid_confirmation_menu(language),
        )
        return

    if order["status"] == "awaiting_receipt":
        if order["payment_method"] is None:
            send_order_summary(token, chat_id, language, order)
        else:
            send_message(token, chat_id, messages["receipt_prompt"], main_menu(language))
        return

    send_message(token, chat_id, messages["unknown"], main_menu(language))


def answer_callback(token: str, callback_id: str, text: str, show_alert: bool = False) -> None:
    telegram_call(
        token,
        "answerCallbackQuery",
        {
            "callback_query_id": callback_id,
            "text": text,
            "show_alert": show_alert,
        },
    )


def process_callback_query(
    token: str,
    admin_id: int,
    callback_query: dict[str, Any],
) -> None:
    callback_id = callback_query.get("id")
    sender = callback_query.get("from") or {}
    actor_id = sender.get("id")
    data = callback_query.get("data") or ""
    message = callback_query.get("message") or {}
    chat = message.get("chat") or {}
    admin_message_id = message.get("message_id")
    language = store.get_user_language(actor_id) if actor_id else None
    if language not in TRANSLATIONS:
        language = "ru"
    messages = TRANSLATIONS[language]

    if not callback_id:
        return
    if actor_id != admin_id or chat.get("id") != admin_id:
        answer_callback(token, callback_id, messages["admin_only"], show_alert=True)
        return

    parts = data.split(":")
    if (
        len(parts) != 3
        or parts[0] != "ffh"
        or parts[1] not in {"approve", "reject"}
        or not parts[2].isdigit()
        or not admin_message_id
    ):
        answer_callback(token, callback_id, messages["order_not_pending"], show_alert=True)
        return

    new_status = "paid" if parts[1] == "approve" else "rejected"
    order, result = store.moderate_order(
        int(parts[2]),
        int(admin_message_id),
        new_status,
    )
    if result != "updated" or not order:
        answer_callback(token, callback_id, messages["order_not_pending"], show_alert=True)
        return

    callback_text = (
        messages["approved_admin"]
        if new_status == "paid"
        else messages["rejected_admin"]
    )
    answer_callback(token, callback_id, callback_text)

    try:
        telegram_call(
            token,
            "editMessageReplyMarkup",
            {
                "chat_id": admin_id,
                "message_id": admin_message_id,
                "reply_markup": {"inline_keyboard": []},
            },
        )
    except TelegramAPIError:
        logging.warning(
            "Could not remove review buttons from the admin message for order %s.",
            order["order_id"],
        )

    customer_language = order["language"]
    if customer_language not in TRANSLATIONS:
        customer_language = "ru"
    send_message(
        token,
        order["chat_id"],
        TRANSLATIONS[customer_language][
            "approved_customer" if new_status == "paid" else "rejected_customer"
        ].format(order_id=order["order_id"]),
        main_menu(customer_language),
    )


def notify_expired_orders(token: str) -> None:
    try:
        expired_orders = store.cancel_expired_orders()
    except Exception:
        logging.exception("Could not cancel expired FF Helper orders.")
        return

    for order in expired_orders:
        language = order["language"]
        if language not in TRANSLATIONS:
            language = "ru"
        try:
            send_message(
                token,
                order["chat_id"],
                TRANSLATIONS[language]["order_expired"].format(
                    order_id=order["order_id"]
                ),
                main_menu(language),
            )
        except TelegramAPIError:
            logging.warning(
                "Could not send the expiration notice for order %s.",
                order["order_id"],
            )


def main() -> int:
    configuration = load_configuration()
    if configuration is None:
        return 1
    token, admin_id, payment_details = configuration
    web_server.start()

    try:
        store.initialize_store()
    except Exception:
        logging.exception("Could not open the FF Helper database.")
        return 1

    logging.info("FF Helper shop is running. Send /start in Telegram to begin.")
    next_update_id: int | None = None

    while True:
        request_data: dict[str, Any] = {
            "timeout": 25,
            "allowed_updates": ["message", "callback_query"],
        }
        if next_update_id is not None:
            request_data["offset"] = next_update_id

        try:
            updates = telegram_call(token, "getUpdates", request_data) or []
            notify_expired_orders(token)
            for update in updates:
                next_update_id = update.get("update_id", 0) + 1
                try:
                    if update.get("message"):
                        process_message(
                            token,
                            admin_id,
                            payment_details,
                            update["message"],
                        )
                    elif update.get("callback_query"):
                        process_callback_query(
                            token,
                            admin_id,
                            update["callback_query"],
                        )
                except TelegramAPIError as error:
                    logging.warning(
                        "Telegram action failed (HTTP %s).",
                        error.status_code or "unknown",
                    )
                except Exception:
                    logging.exception("Could not process a Telegram update.")
        except TelegramAPIError as error:
            if error.status_code == 401:
                logging.error("Telegram rejected the bot token in Replit Secrets.")
                return 1
            logging.warning(
                "Telegram request failed (HTTP %s). Retrying in 5 seconds.",
                error.status_code or "unknown",
            )
            time.sleep(5)
        except (URLError, TimeoutError, OSError):
            logging.warning("Network connection failed. Retrying in 5 seconds.")
            time.sleep(5)


if __name__ == "__main__":
    sys.exit(main())

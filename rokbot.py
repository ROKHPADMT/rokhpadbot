import os
import sqlite3
from datetime import datetime

from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

DB_FILE = "rokhpadbot.db"

SERVICE, PROBLEM, AREA, LOCATION, PHONE, CONFIRM, EXPERT_PHONE = range(7)


MAIN_KEYBOARD = [
    ["🔧 درخواست سرویس"],
    ["💾 بازیابی اطلاعات"],
    ["📞 صحبت با کارشناس"],
    ["ℹ️ خدمات رخپاد"],
]

SERVICE_KEYBOARD = [
    ["🔧 مشکل کامپیوتر / لپ‌تاپ"],
    ["💾 بازیابی اطلاعات"],
    ["🖨️ پرینتر و تجهیزات"],
    ["🌐 شبکه و اینترنت"],
    ["❌ لغو"],
]

LOCATION_KEYBOARD = [
    ["🏠 منزل"],
    ["🏢 محل کار"],
    ["❌ لغو"],
]

CONFIRM_KEYBOARD = [
    ["✅ تأیید و ثبت درخواست"],
    ["❌ لغو"],
]


def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            service TEXT,
            problem TEXT,
            area TEXT,
            location TEXT,
            phone TEXT,
            created_at TEXT
        )
    """)

    conn.commit()
    conn.close()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام 👋\n"
        "به ربات خدمات کامپیوتری رخپاد خوش آمدید.\n\n"
        "لطفاً نوع خدمت مورد نیاز خود را انتخاب کنید:",
        reply_markup=ReplyKeyboardMarkup(
            MAIN_KEYBOARD,
            resize_keyboard=True
        ),
    )


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "لطفاً یکی از گزینه‌های منو را انتخاب کنید.",
        reply_markup=ReplyKeyboardMarkup(
            MAIN_KEYBOARD,
            resize_keyboard=True
        ),
    )


async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Chat ID شما:\n{update.effective_chat.id}"
    )


async def start_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    await update.message.reply_text(
        "حتماً 👍\n"
        "برای ثبت درخواست، نوع خدمت مورد نیازتان را انتخاب کنید:",
        reply_markup=ReplyKeyboardMarkup(
            SERVICE_KEYBOARD,
            resize_keyboard=True
        ),
    )

    return SERVICE


async def start_expert_call(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    await update.message.reply_text(
        "📞 درخواست تماس با کارشناس\n\n"
        "لطفاً شماره تماس خود را ارسال کنید:",
        reply_markup=ReplyKeyboardMarkup(
            [["❌ لغو"]],
            resize_keyboard=True
        ),
    )

    return EXPERT_PHONE


async def save_expert_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()

    if phone == "❌ لغو":
        return await cancel(update, context)

    user = update.effective_user

    admin_chat_id = os.getenv("ADMIN_CHAT_ID")

    if admin_chat_id:
        notification = (
            "📞 درخواست تماس با کارشناس\n\n"
            f"📱 شماره تماس: {phone}\n"
            f"🆔 شناسه کاربر: {user.id}\n"
            f"👤 نام کاربری: @{user.username if user.username else 'بدون نام کاربری'}"
        )

        try:
            await context.bot.send_message(
                chat_id=int(admin_chat_id),
                text=notification
            )
        except Exception as e:
            print(f"Expert call notification error: {e}")

    await update.message.reply_text(
        "✅ درخواست تماس شما ثبت شد.\n\n"
        "کارشناس رخپاد در اولین فرصت با شما تماس خواهد گرفت.",
        reply_markup=ReplyKeyboardMarkup(
            MAIN_KEYBOARD,
            resize_keyboard=True
        ),
    )

    context.user_data.clear()

    return ConversationHandler.END


async def get_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    service = update.message.text

    if service == "❌ لغو":
        return await cancel(update, context)

    context.user_data["service"] = service

    await update.message.reply_text(
        "لطفاً مشکل یا درخواست خود را در چند جمله توضیح دهید:",
        reply_markup=ReplyKeyboardMarkup(
            [["❌ لغو"]],
            resize_keyboard=True
        ),
    )

    return PROBLEM


async def get_problem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ لغو":
        return await cancel(update, context)

    context.user_data["problem"] = update.message.text

    await update.message.reply_text(
        "محدوده یا منطقه شما در تهران چیست؟\n"
        "مثلاً: صادقیه، تهرانپارس، ونک، مرکز تهران و..."
    )

    return AREA


async def get_area(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["area"] = update.message.text

    await update.message.reply_text(
        "خدمت در کجا انجام شود؟",
        reply_markup=ReplyKeyboardMarkup(
            LOCATION_KEYBOARD,
            resize_keyboard=True
        ),
    )

    return LOCATION


async def get_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    location = update.message.text

    if location == "❌ لغو":
        return await cancel(update, context)

    context.user_data["location"] = location

    await update.message.reply_text(
        "لطفاً شماره تماس خود را وارد کنید:"
    )

    return PHONE


async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()

    if phone == "❌ لغو":
        return await cancel(update, context)

    context.user_data["phone"] = phone

    data = context.user_data

    summary = (
        "📋 اطلاعات درخواست\n\n"
        f"🔧 خدمت: {data['service']}\n"
        f"📝 مشکل: {data['problem']}\n"
        f"📍 محدوده: {data['area']}\n"
        f"🏠 محل خدمت: {data['location']}\n"
        f"📞 شماره تماس: {data['phone']}\n\n"
        "آیا اطلاعات بالا صحیح است؟"
    )

    await update.message.reply_text(
        summary,
        reply_markup=ReplyKeyboardMarkup(
            CONFIRM_KEYBOARD,
            resize_keyboard=True
        ),
    )

    return CONFIRM


async def confirm_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ لغو":
        return await cancel(update, context)

    if update.message.text != "✅ تأیید و ثبت درخواست":
        await update.message.reply_text(
            "لطفاً یکی از گزینه‌های نمایش‌داده‌شده را انتخاب کنید."
        )
        return CONFIRM

    data = context.user_data
    user = update.effective_user

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO requests
        (user_id, username, service, problem, area, location, phone, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user.id,
        user.username or "",
        data["service"],
        data["problem"],
        data["area"],
        data["location"],
        data["phone"],
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    ))

    request_id = cur.lastrowid

    conn.commit()
    conn.close()

    # اعلان مدیر
    admin_chat_id = os.getenv("ADMIN_CHAT_ID")

    if admin_chat_id:
        notification = (
            "🔔 درخواست جدید رخپاد\n\n"
            f"🆔 شماره درخواست: #{request_id}\n"
            f"🔧 خدمت: {data['service']}\n"
            f"📝 مشکل: {data['problem']}\n"
            f"📍 محدوده: {data['area']}\n"
            f"🏠 محل خدمت: {data['location']}\n"
            f"📞 شماره تماس: {data['phone']}\n"
            f"👤 کاربر: @{user.username if user.username else 'بدون نام کاربری'}"
        )

        try:
            await context.bot.send_message(
                chat_id=int(admin_chat_id),
                text=notification
            )
        except Exception as e:
            print(f"Admin notification error: {e}")

    await update.message.reply_text(
        f"✅ درخواست شما با موفقیت ثبت شد.\n\n"
        f"شماره درخواست: #{request_id}\n\n"
        "رخپاد در اولین فرصت برای هماهنگی با شما تماس خواهد گرفت.",
        reply_markup=ReplyKeyboardMarkup(
            MAIN_KEYBOARD,
            resize_keyboard=True
        ),
    )

    context.user_data.clear()

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    await update.message.reply_text(
        "درخواست لغو شد.",
        reply_markup=ReplyKeyboardMarkup(
            MAIN_KEYBOARD,
            resize_keyboard=True
        ),
    )

    return ConversationHandler.END


async def button_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "ℹ️ خدمات رخپاد":
        await update.message.reply_text(
            "خدمات رخپاد:\n"
            "🔧 تعمیر و سرویس کامپیوتر و لپ‌تاپ\n"
            "💾 بازیابی اطلاعات\n"
            "🖨️ پرینتر و تجهیزات\n"
            "🌐 شبکه و اینترنت",
        )
        return

    await update.message.reply_text(
        "لطفاً از گزینه‌های منو استفاده کنید.",
        reply_markup=ReplyKeyboardMarkup(
            MAIN_KEYBOARD,
            resize_keyboard=True
        ),
    )

init_db()

app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("menu", menu))
app.add_handler(CommandHandler("myid", myid))

conversation_handler = ConversationHandler(
    entry_points=[
        MessageHandler(
            filters.Regex("^🔧 درخواست سرویس$"),
            start_request
        ),
        MessageHandler(
            filters.Regex("^📞 صحبت با کارشناس$"),
            start_expert_call
        ),
    ],
    states={
        SERVICE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, get_service)
        ],
        PROBLEM: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, get_problem)
        ],
        AREA: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, get_area)
        ],
        LOCATION: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, get_location)
        ],
        PHONE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)
        ],
        CONFIRM: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_request)
        ],
        EXPERT_PHONE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, save_expert_phone)
        ],
    },
    fallbacks=[
        CommandHandler("cancel", cancel),
        MessageHandler(filters.Regex("^❌ لغو$"), cancel),
    ],
)

app.add_handler(conversation_handler)
app.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, button_router)
)

print("ROKHPADbot is running...")

app.run_polling()
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton

from database import init_db, save_audit, get_all_audits, mark_as_viewed, delete_audit, get_audit_by_id

API_TOKEN = "7616949917:AAGa_wr563cBlUiDjsfhECIg67Gvgabu6x8"  # вставь свой токен
ADMINS = [649229459,414108537]  # сюда свои ID админов

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# =======================
# FSM для аудита
# =======================
class AuditForm(StatesGroup):
    channel = State()
    subscribers = State()
    goal = State()


# =======================
# Динамическое главное меню
# =======================
def get_main_menu(user_id: int) -> ReplyKeyboardMarkup:
    keyboard = [
        [
            KeyboardButton(text="🔍 Контент-план"),
            KeyboardButton(text="📝 План")
        ],
        [
            KeyboardButton(text="📈 Запуск"),
            KeyboardButton(text="✉️ Написать")
        ],
        [
            KeyboardButton(text="💰 Цена")
        ]
    ]

    # добавляем кнопку только для админа
    if user_id in ADMINS:
        keyboard.append([KeyboardButton(text="⚙️ Админ")])

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


# =======================
# Команды бота
# =======================
async def set_commands():
    from aiogram.types import BotCommand
    commands = []
    await bot.set_my_commands(commands)


# =======================
# Глобальные команды
# =======================
@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Привет! 👋\nЯ — бот канала @channelUP.\nПомогаю авторам вырасти с 0 до 10K+ без рекламы.",
        reply_markup=get_main_menu(message.from_user.id),
    )


@dp.message(F.text == "💰 Цена")
async def cmd_price(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        """Фикса (1000–1500 руб)— за старт:  
• Глубокий аудит канала  
• Персональный контент-план на 2 недели  
• Поиск точек роста без бюджета  

Процент (30–50%)— от всех доходов:  
— Реклама, партнёрки, подписки  

Почему так?  
✓ Ты видишь результат до оплаты — фикса подтверждает серьёзность  
✓ Я вкладываю время только в рабочие проекты  
✓ Ты контролируешь каждую сделку  

Хочешь проверить, работает ли это?  
Напиши «Старт» — сделаю аудит бесплатно.  
Если канал имеет потенциал — предложу сотрудничество.  

P.S. Фикса не возвращается, но я беру её только если уверен в результате. Потому что мой процент зависит от твоего дохода."""
    )


@dp.message(F.text == "📝 План")
async def cmd_plan(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("📝 Заглушка")


@dp.message(F.text == "📈 Запуск")
async def cmd_launch(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        """🚀 Запуск роста

Не просто расскажу, как расти.  
Я запущу первую точку входа за тебя.

Что сделаю:
1. Проанализирую твой канал
2. Найду 2–3 канала для кросса
3. Свяжусь с авторами
4. Договорюсь о публикации

Ты получишь живых подписчиков — без бюджета.

Хочешь? Нажимай на кнопку "✉️ Написать"

Запускаем."""  
    )


@dp.message(F.text == "✉️ Написать")
async def cmd_contact(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Хочешь обсудить сотрудничество? 🤝\n\n"
        "Пиши продюсеру: @твой_ник\n"
        "(отвечаю в течение дня)\n\n"
        "P.S. Работаю за % от прибыли канала."
    )


@dp.message(F.text == "🔍 Контент-план")
async def cmd_audit(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Отлично!\nСделаю план на 2 недели под твой канал.\n\nДля этого заполни небольшую анкету:\n"
        "1. Напиши @свой_канал ✍️"
    )
    await state.set_state(AuditForm.channel)


# =======================
# FSM: шаги аудита
# =======================
@dp.message(StateFilter(AuditForm.channel))
async def process_channel(message: Message, state: FSMContext):
    await state.update_data(channel=message.text)
    await message.answer("2. Сколько у тебя подписчиков?")
    await state.set_state(AuditForm.subscribers)


@dp.message(StateFilter(AuditForm.subscribers))
async def process_subs(message: Message, state: FSMContext):
    await state.update_data(subscribers=message.text)
    await message.answer("3. Какая цель? (Рост / Монетизация)")
    await state.set_state(AuditForm.goal)


@dp.message(StateFilter(AuditForm.goal))
async def process_goal(message: Message, state: FSMContext):
    await state.update_data(goal=message.text)
    data = await state.get_data()

    await save_audit(
        user_id=message.from_user.id,
        username=message.from_user.username or "unknown",
        channel=data.get('channel', 'не указано'),
        subscribers=data.get('subscribers', 'не указано'),
        goal=data.get('goal', 'не указано')
    )

# Уведомление админам
    notify_text = (
        f"🆕 Новая заявка!\n\n"
        f"👤 Пользователь: @{message.from_user.username or 'unknown'}\n"
        f"📌 Канал: {data.get('channel')}\n"
        f"👥 Подписчики: {data.get('subscribers')}\n"
        f"🎯 Цель: {data.get('goal')}"
    )
    for admin_id in ADMINS:
        try:
            await bot.send_message(admin_id, notify_text)
        except Exception as e:
            print(f"[ERROR] Не удалось отправить уведомление админу {admin_id}: {e}")

    await message.answer(
        f"Спасибо! Заявка создана ✅\n\n"
        f"📌 Канал: {data.get('channel')}\n"
        f"👥 Подписчики: {data.get('subscribers')}\n"
        f"🎯 Цель: {data.get('goal')}\n\n"
        "Через 1-2 часа пришлю отчёт и предложение!",
        reply_markup=get_main_menu(message.from_user.id),
    )
    await state.clear()


# =======================
# Админ-панель
# =======================
@dp.message(F.text == "⚙️ Админ")
async def cmd_admin(message: Message):
    if message.from_user.id not in ADMINS:
        await message.answer("⛔ У вас нет доступа к админ-панели.")
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 Список заявок", callback_data="show_audits")]
        ]
    )
    await message.answer("⚙️ Админ-панель", reply_markup=kb)


@dp.callback_query(F.data == "show_audits")
async def cb_show_audits(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return await callback.answer("⛔ Нет доступа", show_alert=True)

    audits = await get_all_audits()
    if not audits:
        return await callback.message.edit_text("Нет заявок.")

    text = "📋 Заявки:\n\n"
    kb = []
    for idx, (id_, user_id, username, channel, subscribers, goal, viewed) in enumerate(audits, start=1):
        text += f"{idx}. @{username}\nПросмотрена: {'✅' if viewed else '❌'}\n---\n"
        kb.append([
            InlineKeyboardButton(text=f"👁 Просмотреть {idx}", callback_data=f"view_{id_}"),
            InlineKeyboardButton(text=f"🗑 Удалить {idx}", callback_data=f"del_{id_}")
        ])
    markup = InlineKeyboardMarkup(inline_keyboard=kb)
    await callback.message.edit_text(text, reply_markup=markup)


@dp.callback_query(F.data.startswith("view_"))
async def cb_view_audit(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return await callback.answer("⛔ Нет доступа", show_alert=True)

    audit_id = int(callback.data.split("_")[1])
    audit = await get_audit_by_id(audit_id)
    if not audit:
        return await callback.answer("❌ Заявка не найдена", show_alert=True)

    _, user_id, username, channel, subscribers, goal, viewed = audit
    text = (
        f"👤 Пользователь: @{username}\n"
        f"📌 Канал: {channel}\n"
        f"👥 Подписчики: {subscribers}\n"
        f"🎯 Цель: {goal}\n"
        f"Просмотрена: {'✅' if viewed else '❌'}"
    )
    await callback.message.answer(text, reply_markup=get_main_menu(callback.from_user.id))
    await mark_as_viewed(audit_id)
    await callback.answer()


@dp.callback_query(F.data.startswith("del_"))
async def cb_delete_audit(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return await callback.answer("⛔ Нет доступа", show_alert=True)

    audit_id = int(callback.data.split("_")[1])
    await delete_audit(audit_id)
    await callback.answer("✅ Заявка удалена")
    await cb_show_audits(callback)


# =======================
# Прочие сообщения
# =======================
@dp.message()
async def catch_all(message: Message, state: FSMContext):
    current = await state.get_state()
    text = message.text or ""

    if current is None and not text.startswith("/"):
        await message.answer(
            "К сожалению я не смог распознать Вашу команду. Воспользуйтесь кнопками в меню или отправьте /start.",
            reply_markup=get_main_menu(message.from_user.id),
        )


# =======================
# Запуск
# =======================
async def main():
    await init_db()
    await set_commands()
    print("✅ Бот запущен и ждёт команд...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
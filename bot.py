import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.client.default import DefaultBotProperties
from config import API_TOKEN
from aiohttp import ClientConnectorError
from tenacity import retry, stop_after_attempt, wait_exponential

# Настройка логирования (минимальное, чтобы не нагружать CPU)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),  # Сохраняем логи в файл
        logging.StreamHandler()  # Выводим логи в консоль
    ]
)
logger = logging.getLogger(__name__)

# FSM-состояния
class SupportForm(StatesGroup):
    Language = State()
    Issue = State()
    Wallet = State()

# Инициализация бота с оптимизированными параметрами
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode='HTML'))
storage = MemoryStorage()
dp = Dispatcher(bot=bot, storage=storage)

# Переводы
translations = {
    'en': {
        'start': "<b>🍣 Sushi Help Center</b>\n\n👋 Hello, {name}! Welcome to our support bot.\nPlease choose your language:\n---\nUse /start to restart anytime.",
        'welcome': "🌟 Thanks for choosing {lang_name}! Let's solve your issue.\n---\nPlease select the type of your issue:",
        'issue': "Great! Please choose the type of your issue:",
        'wallet': "📩 Please provide your wallet address:",
        'processing': "🔄 Please wait... Processing your request.",
        'operator': "❗️If you have any questions or need assistance, please contact our operator directly:\n\n👤 @sushi_helpcenter_06\nThey’ll help you faster and more efficiently.",
        'restart': "🔁 Start over",
        'back': "⬅️ Back",
        'wallet_too_long': "⚠️ Wallet address is too long (max 100 characters). Please try again.",
        'ping': "🏓 Bot is online!",
        'issues': [
            "1️⃣ 🔗 Wallet connection issue",
            "2️⃣ ⏳ Transaction stuck or failed",
            "3️⃣ 💸 Missing funds / wrong balance",
            "4️⃣ 🖼️ Token not displaying",
            "5️⃣ 🐞 Report a bug or leave feedback",
            "6️⃣ 📞 Contact operator"
        ]
    },
    'ru': {
        'start': "<b>🍣 Sushi Help Center</b>\n\n👋 Здравствуйте, {name}! Добро пожаловать в бота поддержки.\nВыберите язык:\n---\nИспользуйте /start для перезапуска.",
        'welcome': "🌟 Спасибо за выбор языка ({lang_name})! Давай решим твою проблему.\n---\nВыбери тип проблемы:",
        'issue': "Отлично! Выберите тип проблемы:",
        'wallet': "📩 Пожалуйста, укажите адрес вашего кошелька:",
        'processing': "🔄 Пожалуйста, подождите... Обрабатываем ваш запрос.",
        'operator': "❗️Если у вас возникли вопросы или нужна помощь — свяжитесь с оператором лично:\n\n👤 @sushi_helpcenter_06\nОн подскажет и решит ваш вопрос быстрее.",
        'restart': "🔁 Начать заново",
        'back': "⬅️ Назад",
        'wallet_too_long': "⚠️ Адрес кошелька слишком длинный (максимум 100 символов). Попробуйте снова.",
        'ping': "🏓 Бот онлайн!",
        'issues': [
            "1️⃣ 🔗 Не подключается кошелёк",
            "2️⃣ ⏳ Транзакция зависла или обмен не прошёл",
            "3️⃣ 💸 Пропали средства / некорректный баланс",
            "4️⃣ 🖼️ Токен не отображается",
            "5️⃣ 🐞 Сообщить об ошибке или оставить отзыв",
            "6️⃣ 📞 Связаться с оператором"
        ]
    },
    'es': {
        'start': "<b>🍣 Sushi Help Center</b>\n\n👋 ¡Hola, {name}! Bienvenido al bot de soporte.\nSelecciona tu idioma:\n---\nUsa /start para reiniciar en cualquier momento.",
        'welcome': "🌟 ¡Gracias por elegir {lang_name}! Vamos a resolver tu problema.\n---\nElige el tipo de problema:",
        'issue': "¡Perfecto! Elige el tipo de problema:",
        'wallet': "📩 Por favor, proporciona la dirección de tu billetera:",
        'processing': "🔄 Espere por favor... Procesando su solicitud.",
        'operator': "❗️Si tiene preguntas o necesita ayuda, comuníquese directamente con nuestro operador:\n\n👤 @sushi_helpcenter_06\nÉl te ayudará más rápido y eficazmente.",
        'restart': "🔁 Empezar de nuevo",
        'back': "⬅️ Volver",
        'wallet_too_long': "⚠️ La dirección de la billetera es demasiado larga (máximo 100 caracteres). Inténtalo de nuevo.",
        'ping': "🏓 ¡El bot está en línea!",
        'issues': [
            "1️⃣ 🔗 Problema de conexión de billetera",
            "2️⃣ ⏳ Transacción atascada o fallida",
            "3️⃣ 💸 Fondos desaparecidos / saldo incorrecto",
            "4️⃣ 🖼️ Token no visible",
            "5️⃣ 🐞 Informar error o dejar comentario",
            "6️⃣ 📞 Contactar con operador"
        ]
    },
    'zh': {
        'start': "<b>🍣 Sushi Help Center</b>\n\n👋 你好，{name}！欢迎使用我们的支持机器人。\n请选择您的语言：\n---\n随时使用 /start 重新开始。",
        'welcome': "🌟 感谢选择 {lang_name}！让我们解决您的问题。\n---\n请选择您的问题类型：",
        'issue': "很好！请选择您的问题类型：",
        'wallet': "📩 请输入您的钱包地址：",
        'processing': "🔄 请稍候... 正在处理您的请求。",
        'operator': "❗️如有任何问题或需要帮助，请直接联系我们的客服人员：\n\n👤 @sushi_helpcenter_06\n他们会更快更有效地帮助您。",
        'restart': "🔁 重新开始",
        'back': "⬅️ 返回",
        'wallet_too_long': "⚠️ 钱包地址过长（最多100个字符）。请重试。",
        'ping': "🏓 机器人在线！",
        'issues': [
            "1️⃣ 🔗 钱包连接问题",
            "2️⃣ ⏳ 交易卡住或失败",
            "3️⃣ 💸 资金丢失 / 余额错误",
            "4️⃣ 🖼️ 代币未显示",
            "5️⃣ 🐞 报告错误或留下反馈",
            "6️⃣ 📞 联系客服"
        ]
    },
    'fr': {
        'start': "<b>🍣 Sushi Help Center</b>\n\n👋 Bonjour, {name} ! Bienvenue sur le bot de support.\nVeuillez choisir votre langue :\n---\nUtilisez /start pour redémarrer à tout moment.",
        'welcome': "🌟 Merci d'avoir choisi {lang_name} ! Résolvons votre problème.\n---\nChoisissez le type de problème :",
        'issue': "Parfait ! Choisissez le type de problème :",
        'wallet': "📩 Veuillez fournir l'adresse de votre portefeuille :",
        'processing': "🔄 Veuillez patienter... Traitement de votre demande.",
        'operator': "❗️Si vous avez des questions ou besoin d’aide, contactez directement notre opérateur :\n\n👤 @sushi_helpcenter_06\nIl vous aidera plus rapidement et efficacement.",
        'restart': "🔁 Recommencer",
        'back': "⬅️ Retour",
        'wallet_too_long': "⚠️ L'adresse du portefeuille est trop longue (maximum 100 caractères). Veuillez réessayer.",
        'ping': "🏓 Le bot est en ligne !",
        'issues': [
            "1️⃣ 🔗 Problème de connexion au portefeuille",
            "2️⃣ ⏳ Transaction bloquée ou échouée",
            "3️⃣ 💸 Fonds manquants / solde incorrect",
            "4️⃣ 🖼️ Jeton non affiché",
            "5️⃣ 🐞 Signaler un bug ou donner un avis",
            "6️⃣ 📞 Contacter un opérateur"
        ]
    }
}

# Кэширование клавиатуры языков (создаём один раз)
lang_buttons = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="🇬🇧 English", callback_data='lang_en'),
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data='lang_ru')
    ],
    [
        InlineKeyboardButton(text="🇪🇸 Español", callback_data='lang_es'),
        InlineKeyboardButton(text="🇨🇳 中文", callback_data='lang_zh')
    ],
    [
        InlineKeyboardButton(text="🇫🇷 Français", callback_data='lang_fr')
    ]
])

# Словарь для названий языков
lang_names = {
    'en': 'English',
    'ru': 'Русский',
    'es': 'Español',
    'zh': '中文',
    'fr': 'Français'
}

# Команда /ping для проверки работоспособности
@dp.message(Command("ping"))
async def cmd_ping(message: Message, state: FSMContext):
    lang = (await state.get_data()).get('lang', 'en')
    await message.answer(translations[lang]['ping'])
    logger.info(f"User {message.from_user.id} sent /ping")

# /start
@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    try:
        logger.info(f"Processing /start for user {message.from_user.id}")
        # Сбрасываем состояние, если оно уже существует
        await state.set_state(None)
        name = message.from_user.first_name or "User"
        await message.answer(translations['en']['start'].format(name=name), reply_markup=lang_buttons)
        await state.set_state(SupportForm.Language)
        logger.info(f"User {message.from_user.id} successfully started the bot")
    except Exception as e:
        logger.error(f"Error in /start for user {message.from_user.id}: {e}")
        await message.answer("An error occurred. Please try again later.")

# Выбор языка
@dp.callback_query(lambda c: c.data.startswith('lang_'), StateFilter(SupportForm.Language))
async def process_language_callback(callback_query: types.CallbackQuery, state: FSMContext):
    try:
        lang = callback_query.data.split('_')[1]
        await state.update_data(lang=lang)

        # Создаём клавиатуру для проблем с кнопкой "Назад"
        issues_markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=issue, callback_data=f"issue_{i}")] for i, issue in enumerate(translations[lang]['issues'])
        ] + [[InlineKeyboardButton(text=translations[lang]['back'], callback_data='back_to_lang')]])

        await bot.send_message(
            callback_query.from_user.id,
            translations[lang]['welcome'].format(lang_name=lang_names[lang]),
            reply_markup=issues_markup
        )
        await state.set_state(SupportForm.Issue)
        logger.info(f"User {callback_query.from_user.id} selected language: {lang}")
    except Exception as e:
        logger.error(f"Error in language selection for user {callback_query.from_user.id}: {e}")
        await bot.send_message(callback_query.from_user.id, "An error occurred. Please try /start again.")

# Выбор типа проблемы
@dp.callback_query(lambda c: c.data.startswith('issue_'), StateFilter(SupportForm.Issue))
async def process_issue_callback(callback_query: types.CallbackQuery, state: FSMContext):
    try:
        user_data = await state.get_data()
        lang = user_data.get('lang', 'en')  # Fallback на 'en', если lang отсутствует
        issue_index = int(callback_query.data.split('_')[1])
        issue_text = translations[lang]['issues'][issue_index]
        await state.update_data(issue=issue_text)

        # Добавляем кнопку "Назад" для возврата к выбору проблемы
        wallet_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=translations[lang]['back'], callback_data='back_to_issue')]
        ])

        await bot.send_message(callback_query.from_user.id, translations[lang]['wallet'], reply_markup=wallet_kb)
        await state.set_state(SupportForm.Wallet)
        logger.info(f"User {callback_query.from_user.id} selected issue: {issue_text}")
    except Exception as e:
        logger.error(f"Error in issue selection for user {callback_query.from_user.id}: {e}")
        await bot.send_message(callback_query.from_user.id, "An error occurred. Please try /start again.")

# Обработчик кнопок "Назад"
@dp.callback_query(lambda c: c.data in ['back_to_lang', 'back_to_issue'], StateFilter('*'))
async def process_back_callback(callback_query: types.CallbackQuery, state: FSMContext):
    try:
        user_data = await state.get_data()
        lang = user_data.get('lang', 'en')  # Fallback на 'en'

        if callback_query.data == 'back_to_lang':
            name = callback_query.from_user.first_name or "User"
            await bot.send_message(
                callback_query.from_user.id,
                translations[lang]['start'].format(name=name),
                reply_markup=lang_buttons
            )
            await state.set_state(SupportForm.Language)
            logger.info(f"User {callback_query.from_user.id} went back to language selection")
        elif callback_query.data == 'back_to_issue':
            issues_markup = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=issue, callback_data=f"issue_{i}")] for i, issue in enumerate(translations[lang]['issues'])
            ] + [[InlineKeyboardButton(text=translations[lang]['back'], callback_data='back_to_lang')]])
            await bot.send_message(
                callback_query.from_user.id,
                translations[lang]['welcome'].format(lang_name=lang_names[lang]),
                reply_markup=issues_markup
            )
            await state.set_state(SupportForm.Issue)
            logger.info(f"User {callback_query.from_user.id} went back to issue selection")
    except Exception as e:
        logger.error(f"Error in back navigation for user {callback_query.from_user.id}: {e}")
        await bot.send_message(callback_query.from_user.id, "An error occurred. Please try /start again.")

# Ввод кошелька и финальное сообщение
@dp.message(StateFilter(SupportForm.Wallet))
async def process_wallet(message: Message, state: FSMContext):
    try:
        user_data = await state.get_data()
        lang = user_data.get('lang', 'en')
        wallet = message.text

        # Проверка длины адреса кошелька
        if len(wallet) > 100:
            wallet_kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=translations[lang]['back'], callback_data='back_to_issue')]
            ])
            await message.answer(translations[lang]['wallet_too_long'], reply_markup=wallet_kb)
            logger.info(f"User {message.from_user.id} entered too long wallet address")
            return

        issue = user_data.get('issue', 'Unknown issue')

        restart_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=translations[lang]['restart'], callback_data='restart')]
        ])

        # Анимация обработки с эмодзи
        processing_msg = await message.answer("🔄 Processing...")
        await asyncio.sleep(1)
        await bot.edit_message_text("⏳ Processing...", chat_id=message.chat.id, message_id=processing_msg.message_id)
        await asyncio.sleep(1)
        await bot.edit_message_text("✅ Processed!", chat_id=message.chat.id, message_id=processing_msg.message_id)
        await asyncio.sleep(0.5)
        await message.answer(translations[lang]['operator'], reply_markup=restart_kb)
        logger.info(f"User {message.from_user.id} submitted wallet: {wallet}, issue: {issue}")
    except Exception as e:
        logger.error(f"Error in wallet processing for user {message.from_user.id}: {e}")
        await message.answer("An error occurred. Please try /start again.")

# Кнопка "Начать заново"
@dp.callback_query(lambda c: c.data == 'restart', StateFilter('*'))
async def restart_bot(callback_query: types.CallbackQuery, state: FSMContext):
    try:
        await state.set_state(None)
        name = callback_query.from_user.first_name or "User"
        await bot.send_message(
            callback_query.from_user.id,
            translations['en']['start'].format(name=name),
            reply_markup=lang_buttons
        )
        await state.set_state(SupportForm.Language)
        logger.info(f"User {callback_query.from_user.id} restarted the bot")
    except Exception as e:
        logger.error(f"Error in restart for user {callback_query.from_user.id}: {e}")
        await bot.send_message(callback_query.from_user.id, "An error occurred. Please try /start again.")

# Очистка состояния каждые 30 минут
async def clear_old_states():
    while True:
        await asyncio.sleep(1800)  # 30 минут
        try:
            # Очищаем данные в памяти
            storage.data.clear()
            logger.info("Successfully cleared old states")
        except Exception as e:
            logger.error(f"Error clearing old states: {e}")

# Функция для запуска при старте с повторными попытками
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def on_startup(_):
    logger.info("Bot is online, scheduling tasks...")
    try:
        await bot.get_me()  # Проверяем подключение к Telegram
        logger.info("Successfully connected to Telegram API")
    except ClientConnectorError as e:
        logger.error(f"Failed to connect to Telegram API: {e}")
        raise
    asyncio.create_task(clear_old_states())

# Запуск
async def main():
    try:
        await dp.start_polling(bot)
    except ClientConnectorError as e:
        logger.error(f"Failed to start polling due to network error: {e}")
        logger.info("Retrying in 10 seconds...")
        await asyncio.sleep(10)
        await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
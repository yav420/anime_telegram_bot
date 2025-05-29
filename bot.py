import logging
import os
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from api_client import AnimeAPIClient
from config import TOKEN

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Создаем папку для логов, если ее нет
if not os.path.exists('logs'):
    os.makedirs('logs')

class DialogLogger:
    @staticmethod
    def log(user_id: int, message: str, is_bot: bool = False):
        log_file = f'logs/user_{user_id}.log'
        prefix = 'BOT' if is_bot else 'USER'
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f'{timestamp} {prefix}: {message}\n')

def get_main_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("Поиск аниме"), KeyboardButton("Топ аниме")],
        [KeyboardButton("Случайное аниме"), KeyboardButton("Помощь")]
    ], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_text = (
        f"Привет, {user.first_name}! Я бот для поиска информации об аниме.\n\n"
        "Используй кнопки ниже для взаимодействия:"
    )
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=welcome_text,
        reply_markup=get_main_keyboard()
    )
    
    DialogLogger.log(user.id, "/start")
    DialogLogger.log(user.id, welcome_text, is_bot=True)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📋 Доступные команды:\n\n"
        "🔍 Поиск аниме - найти аниме по названию\n"
        "🏆 Топ аниме - показать лучшие аниме\n"
        "🎲 Случайное аниме - получить случайное аниме\n"
        "ℹ️ Помощь - это сообщение"
    )
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=help_text,
        reply_markup=get_main_keyboard()
    )
    
    DialogLogger.log(update.effective_user.id, "/help")
    DialogLogger.log(update.effective_user.id, help_text, is_bot=True)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    DialogLogger.log(user_id, text)
    
    if text == "Поиск аниме":
        await search_anime(update, context)
    elif text == "Топ аниме":
        await top_anime(update, context)
    elif text == "Случайное аниме":
        await random_anime(update, context)
    elif text == "Помощь":
        await help_command(update, context)
    elif text == "Назад":
        await help_command(update, context)
    else:
        await handle_search_query(update, context)

async def search_anime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="🔍 Введите название аниме для поиска:",
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Назад")]], resize_keyboard=True)
    )
    DialogLogger.log(update.effective_user.id, "Поиск аниме")

async def handle_search_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    query = update.message.text
    
    if query == "Назад":
        await help_command(update, context)
        return
    
    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        anime_list = AnimeAPIClient.search_anime(query)
        
        if not anime_list:
            response = "❌ Аниме не найдено. Попробуйте другое название."
            await update.message.reply_text(response, reply_markup=get_main_keyboard())
            DialogLogger.log(user_id, response, is_bot=True)
            return
        
        keyboard = []
        for anime in anime_list[:5]:
            title = anime['title'][:30] + "..." if len(anime['title']) > 30 else anime['title']
            keyboard.append([InlineKeyboardButton(
                f"{title} ({anime.get('year', 'N/A')})",
                callback_data=f"details_{anime['mal_id']}"
            )])
        
        await update.message.reply_text(
            "🔍 Результаты поиска:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        DialogLogger.log(user_id, "Результаты поиска", is_bot=True)
        
    except Exception as e:
        logger.error(f"Ошибка поиска: {e}")
        response = "⚠️ Произошла ошибка при поиске. Попробуйте позже."
        await update.message.reply_text(response, reply_markup=get_main_keyboard())
        DialogLogger.log(user_id, response, is_bot=True)

async def show_anime_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    try:
        anime_id = query.data.split("_")[1]
        anime = AnimeAPIClient.get_anime_details(anime_id)
        
        if not anime:
            response = "❌ Не удалось получить информацию об аниме."
            await query.edit_message_text(response)
            DialogLogger.log(user_id, response, is_bot=True)
            return
        
        title = anime['title']
        synopsis = anime.get('synopsis', 'Нет описания')
        score = anime.get('score', 'Нет оценки')
        episodes = anime.get('episodes', 'Неизвестно')
        year = anime.get('year', 'Неизвестно')
        
        response = (
            f"🎬 <b>{title}</b> ({year})\n\n"
            f"⭐ Оценка: {score}\n"
            f"📺 Эпизодов: {episodes}\n\n"
            f"📝 Описание:\n{synopsis[:400]}..."
        )
        
        await query.edit_message_text(
            text=response,
            parse_mode='HTML'
        )
        DialogLogger.log(user_id, response, is_bot=True)
        
    except Exception as e:
        logger.error(f"Ошибка деталей: {e}")
        response = "⚠️ Произошла ошибка при получении информации."
        await query.edit_message_text(response)
        DialogLogger.log(user_id, response, is_bot=True)

async def top_anime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    DialogLogger.log(user_id, "Топ аниме")
    
    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        anime_list = AnimeAPIClient.get_top_anime()[:10]
        
        if not anime_list:
            response = "❌ Не удалось получить топ аниме."
            await update.message.reply_text(response, reply_markup=get_main_keyboard())
            DialogLogger.log(user_id, response, is_bot=True)
            return
        
        response = "🏆 Топ аниме:\n\n" + "\n".join(
            f"{i+1}. {anime['title']} ⭐ {anime.get('score', 'N/A')}" 
            for i, anime in enumerate(anime_list)
        )
        
        await update.message.reply_text(
            text=response,
            reply_markup=get_main_keyboard()
        )
        DialogLogger.log(user_id, response, is_bot=True)
        
    except Exception as e:
        logger.error(f"Ошибка топа: {e}")
        response = "⚠️ Произошла ошибка при получении топа аниме."
        await update.message.reply_text(response, reply_markup=get_main_keyboard())
        DialogLogger.log(user_id, response, is_bot=True)

async def random_anime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    DialogLogger.log(user_id, "Случайное аниме")
    
    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        anime = AnimeAPIClient.get_random_anime()
        
        if not anime:
            response = "❌ Не удалось получить случайное аниме."
            await update.message.reply_text(response, reply_markup=get_main_keyboard())
            DialogLogger.log(user_id, response, is_bot=True)
            return
        
        title = anime['title']
        synopsis = anime.get('synopsis', 'Нет описания')
        score = anime.get('score', 'Нет оценки')
        episodes = anime.get('episodes', 'Неизвестно')
        year = anime.get('year', 'Неизвестно')
        
        response = (
            f"🎲 Случайное аниме:\n\n"
            f"🎬 <b>{title}</b> ({year})\n\n"
            f"⭐ Оценка: {score}\n"
            f"📺 Эпизодов: {episodes}\n\n"
            f"📝 Описание:\n{synopsis[:400]}..."
        )
        
        await update.message.reply_text(
            text=response,
            parse_mode='HTML',
            reply_markup=get_main_keyboard()
        )
        DialogLogger.log(user_id, response, is_bot=True)
        
    except Exception as e:
        logger.error(f"Ошибка случайного аниме: {e}")
        response = "⚠️ Произошла ошибка при получении случайного аниме."
        await update.message.reply_text(response, reply_markup=get_main_keyboard())
        DialogLogger.log(user_id, response, is_bot=True)

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Обработчики команд
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.add_handler(CallbackQueryHandler(show_anime_details, pattern="^details_"))
    
    app.run_polling()

if __name__ == "__main__":
    main()

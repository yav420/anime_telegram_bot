import os
from config import LOG_DIR

class DialogLogger:
    @staticmethod
    def ensure_log_dir():
        """Создает директорию для логов, если ее нет"""
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR)
    
    @staticmethod
    def log_message(user_id, message, is_bot=False):
        """Логирует сообщение в файл пользователя"""
        DialogLogger.ensure_log_dir()
        log_file = os.path.join(LOG_DIR, f"{user_id}.log")
        
        with open(log_file, 'a', encoding='utf-8') as f:
            prefix = "BOT" if is_bot else "USER"
            f.write(f"{prefix}: {message}\n")
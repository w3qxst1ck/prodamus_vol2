import os

from loguru import logger

log_folder = "logs"
if not os.path.exists(log_folder):
    os.makedirs(log_folder)

logger.remove()
logger.add(f"{log_folder}/fastapi.log", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {file}:{line} | {message}")
logger.add(f"{log_folder}/fastapi_error.log", level="ERROR", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {file}:{line} | {message}")

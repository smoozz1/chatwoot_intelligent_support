import subprocess
import re
import logging
import time

logger = logging.getLogger(__name__)

def get_localtunnel_url(port=8000, retries=3, timeout=10):
    """
    Запуск локального туннеля и получение публичного URL (синхронно).
    
    :param port: Локальный порт, который открываем.
    :param retries: Количество попыток.
    :param timeout: Максимальное время ожидания URL в секундах.
    :return: публичный URL или None
    """
    for attempt in range(1, retries + 1):
        logger.info(f"Попытка {attempt}: запускаю LocalTunnel на порту {port}...")
        try:
            process = subprocess.Popen(
                ["lt", "--port", str(port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            start_time = time.time()
            while True:
                if time.time() - start_time > timeout:
                    logger.warning("Превышено время ожидания публичного URL")
                    process.terminate()
                    break

                line = process.stdout.readline()
                if not line:
                    continue

                line = line.strip()
                logger.debug(f"LT stdout: {line}")

                match = re.search(r'https://[a-zA-Z0-9.-]+\.loca\.lt', line)
                if match:
                    url = match.group(0)
                    logger.info(f"Публичный URL туннеля: {url}")
                    return url

            stderr = process.stderr.read()
            if stderr:
                logger.warning(f"LT stderr: {stderr.strip()}")

        except Exception as e:
            logger.error(f"Ошибка при запуске LocalTunnel: {e}")

    logger.error("Не удалось получить публичный URL туннеля после всех попыток")
    return None

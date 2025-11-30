import asyncio
import logging
import re
import time
import aiohttp

logger = logging.getLogger(__name__)


class LocalTunnel:
    def __init__(
        self,
        port=8000,
        check_interval=10,
        timeout=10,
        on_url_change=None,
        debounce_interval=3
    ):
        self.port = port
        self.check_interval = check_interval
        self.timeout = timeout
        self.on_url_change = on_url_change

        self.process = None
        self.current_url = None
        self._stop = False

        # debounce
        self._last_url_change_ts = 0
        self._debounce_interval = debounce_interval

    async def start(self):
        asyncio.create_task(self._run())

    async def stop(self):
        self._stop = True
        if self.process:
            logger.info(f"LocalTunnel остановлен, URL: {self.current_url}")
            self.process.kill()

    async def _run(self):
        while not self._stop:
            if not self.process or self.process.returncode is not None:
                logger.warning("Запускаю LocalTunnel...")
                await self._start_tunnel()

            if self.current_url:
                ok = await self._check_tunnel()
                if not ok:
                    logger.error("LocalTunnel URL недоступен. Перезапуск...")
                    await self._restart_tunnel()

            await asyncio.sleep(self.check_interval)

    async def _start_tunnel(self):
        # Запуск lt в subprocess
        self.process = await asyncio.create_subprocess_exec(
            "lt",
            "--port", str(self.port),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        start_time = time.time()
        
        while True:
            if time.time() - start_time > self.timeout:
                logger.error("Не удалось получить публичный URL LocalTunnel")
                self.process.kill()
                return
            
            try:
                line = await asyncio.wait_for(self.process.stdout.readline(), timeout=1)
            except asyncio.TimeoutError:
                continue
            
            if not line:
                await asyncio.sleep(0.1)
                continue
            
            decoded = line.decode().strip()
            
            match = re.search(r"https://[-a-zA-Z0-9]+\.loca\.lt", decoded)
            if match:
                new_url = match.group(0)
                
                # debounce
                now = time.time()
                if (
                    new_url == self.current_url
                    and now - self._last_url_change_ts < self._debounce_interval
                ):
                    logger.info(
                        f"Получен повторный URL {new_url}, но событие проигнорировано (debounce)"
                    )
                    return self.current_url
                
                self._last_url_change_ts = now
                self.current_url = new_url
                
                logger.info(f"Получен новый LocalTunnel URL: {new_url}")
                
                if not await self._check_tunnel():
                    logger.warning(f"URL {new_url} недоступен сразу после запуска. Пропускаю.")
                    return self.current_url
                
                if self.on_url_change:
                    await self.on_url_change(new_url)
                    
                return self.current_url
            
    async def _restart_tunnel(self):
        if self.process:
            self.process.kill()
            try:
                await self.process.wait()
            except Exception:
                pass
            
        self.process = None
        self.current_url = None
        
        await self._start_tunnel()
        
    async def _check_tunnel(self, retries=3, retry_interval=0.5):
        """Проверяет доступность туннеля через GET с несколькими попытками."""
        if not self.current_url:
            return False

        for attempt in range(1, retries + 1):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(self.current_url, timeout=3) as resp:
                        if resp.status < 500:
                            return True
            except Exception as e:
                logger.debug(f"Попытка {attempt} GET {self.current_url} не удалась: {e}")

            await asyncio.sleep(retry_interval)

        logger.warning(f"Туннель {self.current_url} недоступен после {retries} попыток")
        return False


import asyncio
import logging
from sys import stdout

from aiogram import BaseMiddleware
from aiogram.types import Update
from ping3 import ping

import handlers  # noqa: F401
from config import dp, bot, rt, allowed_users, debug, admin_id, cam_host


class UserFilterMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Update, data: dict):
        if event.from_user.id not in allowed_users:
            await event.reply("Извините, но вы не можете пользоваться этим ботом.")
            return None
        return await handler(event, data)


async def on_start():
    await bot.send_message(admin_id, 'Бот запущен.')
    if not ping(cam_host):
        await bot.send_message(admin_id, 'Нет соединения с камерой!')
        logger = logging.getLogger(__name__)
        logger.warning("Нет соединения с камерой!")


async def main():
    match debug:
        case 1:
            level = logging.INFO
        case 0:
            level = logging.ERROR

    logging.basicConfig(level=level,
                        format="%(asctime)s | %(levelname)s: %(message)s",
                        datefmt="%H:%M:%S",
                        stream=stdout)
    dp.message.middleware(UserFilterMiddleware())
    dp.include_router(rt)
    await on_start()
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())

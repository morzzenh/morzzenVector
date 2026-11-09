from asyncio import run

from database import close_db


async def close():
    await close_db()
    return "Все документы из базы данных удалены!"


print(run(close()))

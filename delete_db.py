from database import close_db
from asyncio import run

async def close():
    await close_db()
    return 'Все документы из базы данных удалены!'

run(close())
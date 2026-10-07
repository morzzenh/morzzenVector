import os
from dotenv import load_dotenv
from sqlalchemy import URL

load_dotenv()

# Сборка URL для подключения к базе данных

DATABASE_URL = URL.create(
    drivername=os.getenv('DRIVER_NAME'),
    username=os.getenv('DATABASE_USER'),
    password=os.getenv('DATABASE_PASSWORD'),
    host=os.getenv('DATABASE_HOST'),
    port=os.getenv('DATABASE_PORT'),
    database=os.getenv('DATABASE_NAME')
)
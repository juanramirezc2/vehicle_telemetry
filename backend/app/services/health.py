from fastapi import FastAPI
from sqlalchemy import text


async def check_database(app: FastAPI) -> None:
    async with app.state.db_engine.connect() as connection:
        await connection.execute(text("SELECT 1"))

import aiosqlite

DB_NAME = "audits.db"

# =======================
# Инициализация базы
# =======================
async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS audits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                channel TEXT NOT NULL,
                subscribers TEXT,
                goal TEXT,
                viewed INTEGER DEFAULT 0
            )
        """)
        await db.commit()

# =======================
# Сохранение новой заявки
# =======================
async def save_audit(user_id: int, username: str, channel: str, subscribers: str, goal: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO audits (user_id, username, channel, subscribers, goal) VALUES (?, ?, ?, ?, ?)",
            (user_id, username, channel, subscribers, goal)
        )
        await db.commit()

# =======================
# Получить все заявки
# =======================
async def get_all_audits():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT id, user_id, username, channel, subscribers, goal, viewed FROM audits"
        ) as cursor:
            return await cursor.fetchall()

# =======================
# Получить заявку по ID
# =======================
async def get_audit_by_id(audit_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT id, user_id, username, channel, subscribers, goal, viewed FROM audits WHERE id = ?",
            (audit_id,)
        ) as cursor:
            return await cursor.fetchone()

# =======================
# Пометить заявку как просмотренную
# =======================
async def mark_as_viewed(audit_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE audits SET viewed = 1 WHERE id = ?", (audit_id,))
        await db.commit()

# =======================
# Удалить заявку
# =======================
async def delete_audit(audit_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM audits WHERE id = ?", (audit_id,))
        await db.commit()
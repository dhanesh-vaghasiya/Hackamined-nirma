"""One-time migration to align DB with the new models.py schema."""
from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    with db.engine.begin() as conn:
        # 1. Rename users.password -> password_hash
        conn.execute(text("ALTER TABLE users RENAME COLUMN password TO password_hash"))
        print("OK: users.password -> password_hash")

        # 2. Add missing columns to jobs
        conn.execute(text("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS title_norm VARCHAR(300)"))
        conn.execute(text("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS company VARCHAR(200)"))
        conn.execute(text("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS location_raw VARCHAR(200)"))
        conn.execute(text("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS source VARCHAR(50) DEFAULT 'naukri'"))
        print("OK: added missing jobs columns")

        # 3. Drop typo table chat_messagebs and old chat_messages (different schema)
        conn.execute(text("DROP TABLE IF EXISTS chat_messagebs"))
        conn.execute(text("DROP TABLE IF EXISTS chat_messages"))
        print("OK: dropped old chat tables")

    # 4. Recreate chat_messages with the correct new schema
    from app.models import ChatMessage
    ChatMessage.__table__.create(db.engine, checkfirst=True)
    print("OK: created chat_messages with new schema")

    print("\nAll migrations applied successfully!")

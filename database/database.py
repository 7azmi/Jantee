import os
import psycopg2
from datetime import date
from dotenv import load_dotenv

# Load environment variables
load_dotenv("app/.env")

# Database credentials
db_host = os.environ.get("PGHOST", "your_host")
db_user = os.environ.get("PGUSER", "your_user")
db_password = os.environ.get("PGPASSWORD", "your_password")
db_name = os.environ.get("PGDATABASE", "your_database")

# Database table names
USERS_TABLE = 'users'
GROUPS_TABLE = 'groups'
DAILY_PUSHUP_RECORD_TABLE = 'daily_pushup_record'

GROUP_ID_COLUMN = 'group_id'
PUSHUP_GOAL_COLUMN = 'pushup_goal'
PUNISHMENT_COLUMN = 'punishment'

USER_TELEGRAM_ID_COLUMN = 'user_telegram_id'
DATE_COLUMN = 'date'
PUSHUPS_COUNT_COLUMN = 'pushups_count'

def create_db():
    with psycopg2.connect(host=db_host, user=db_user, password=db_password, database=db_name) as conn:
        c = conn.cursor()
        # Create Users Table
        c.execute(f"""
            CREATE TABLE IF NOT EXISTS {USERS_TABLE} (
                telegram_id INTEGER PRIMARY KEY,
                group_id INTEGER,
                FOREIGN KEY (group_id) REFERENCES {GROUPS_TABLE} (group_id)
            );
        """)
        # Create Groups Table
        c.execute(f"""
            CREATE TABLE IF NOT EXISTS {GROUPS_TABLE} (
                group_id SERIAL PRIMARY KEY,
                pushup_goal INTEGER,
                punishment TEXT
            );
        """)
        # Create Daily Pushup Record Table
        c.execute(f"""
            CREATE TABLE IF NOT EXISTS {DAILY_PUSHUP_RECORD_TABLE} (
                user_telegram_id INTEGER,
                date DATE,
                pushups_count INTEGER,
                PRIMARY KEY (user_telegram_id, date),
                FOREIGN KEY (user_telegram_id) REFERENCES {USERS_TABLE} (telegram_id)
            );
        """)
        conn.commit()

def set_data(table, primary_key, column, new_data, key_value):
    with psycopg2.connect(host=db_host, user=db_user, password=db_password, database=db_name) as conn:
        c = conn.cursor()
        query = f"UPDATE {table} SET {column} = %s WHERE {primary_key} = %s;"
        c.execute(query, (new_data, key_value))
        conn.commit()

def get_data(table, primary_key, column, key_value):
    with psycopg2.connect(host=db_host, user=db_user, password=db_password, database=db_name) as conn:
        c = conn.cursor()
        query = f"SELECT {column} FROM {table} WHERE {primary_key} = %s;"
        c.execute(query, (key_value,))
        result = c.fetchone()
        return result[0] if result else None

def add_daily_pushup_record(user_id, pushups_count):
    with psycopg2.connect(host=db_host, user=db_user, password=db_password, database=db_name) as conn:
        c = conn.cursor()
        c.execute(f"""
            INSERT INTO {DAILY_PUSHUP_RECORD_TABLE} (user_telegram_id, date, pushups_count)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_telegram_id, date) DO UPDATE SET pushups_count = {DAILY_PUSHUP_RECORD_TABLE}.pushups_count + EXCLUDED.pushups_count;
        """, (user_id, date.today(), pushups_count))
        conn.commit()

def add_user(telegram_id, group_id):
    with psycopg2.connect(host=db_host, user=db_user, password=db_password, database=db_name) as conn:
        c = conn.cursor()
        c.execute(f"""
            INSERT INTO {USERS_TABLE} (telegram_id, group_id)
            VALUES (%s, %s) ON CONFLICT (telegram_id) DO NOTHING;
        """, (telegram_id, group_id))
        conn.commit()

def add_group(pushup_goal, punishment):
    with psycopg2.connect(host=db_host, user=db_user, password=db_password, database=db_name) as conn:
        c = conn.cursor()
        c.execute(f"""
            INSERT INTO {GROUPS_TABLE} (pushup_goal, punishment)
            VALUES (%s, %s) RETURNING group_id;
        """, (pushup_goal, punishment))
        group_id = c.fetchone()[0]
        conn.commit()
        return group_id

def get_users_in_group(group_id):
    with psycopg2.connect(host=db_host, user=db_user, password=db_password, database=db_name) as conn:
        c = conn.cursor()
        c.execute(f"SELECT telegram_id FROM {USERS_TABLE} WHERE group_id = %s;", (group_id,))
        return [row[0] for row in c.fetchall()]

if __name__ == "__main__":
    create_db()
    # Example usage
    # group_id = add_group(50, "5-minute plank")
    # add_user(123456789, group_id)
    # add_daily_pushup_record(123456789, 30)
    # print(get_data(USERS_TABLE, 'telegram_id', 'group_id', 123456789))
    # print(get_users_in_group(group_id))

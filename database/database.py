import os
import psycopg2
from datetime import datetime, timedelta

from dotenv import load_dotenv
import pytz

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


def create_db(): # not tested
    with psycopg2.connect(host=db_host, user=db_user, password=db_password, database=db_name) as conn:
        c = conn.cursor()
        # Create Groups Table with an additional 'timezone' field and telegram_id as PK
        c.execute(f"""
            CREATE TABLE IF NOT EXISTS {GROUPS_TABLE} (
                telegram_id INTEGER PRIMARY KEY,  -- Unique and Primary Key
                pushup_goal INTEGER,
                punishment TEXT,
                timezone TEXT
            );
        """)
        # Create Users Table
        c.execute(f"""
            CREATE TABLE IF NOT EXISTS {USERS_TABLE} (
                telegram_id INTEGER PRIMARY KEY,
                group_id INTEGER,
                FOREIGN KEY (group_id) REFERENCES {GROUPS_TABLE} (telegram_id)
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


def create_connection():
    return psycopg2.connect(host=db_host, user=db_user, password=db_password, database=db_name)


def create_row(table_name, data):
    try:
        conn = create_connection()
        c = conn.cursor()
        columns = ', '.join(data.keys())
        values = ', '.join(['%s'] * len(data))
        c.execute(f"INSERT INTO {table_name} ({columns}) VALUES ({values})", list(data.values()))
        conn.commit()
    except psycopg2.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()


def delete_row(table_name, condition):
    try:
        conn = create_connection()
        c = conn.cursor()
        condition_str = ' AND '.join([f"{k} = %s" for k in condition])
        c.execute(f"DELETE FROM {table_name} WHERE {condition_str}", list(condition.values()))
        conn.commit()
    except psycopg2.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()


def set_value(table_name, data, condition):
    try:
        conn = create_connection()
        c = conn.cursor()
        update_str = ', '.join([f"{k} = %s" for k in data])
        condition_str = ' AND '.join([f"{k} = %s" for k in condition])
        c.execute(f"UPDATE {table_name} SET {update_str} WHERE {condition_str}",
                  list(data.values()) + list(condition.values()))
        conn.commit()
    except psycopg2.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()


def get_value(table_name, columns, condition):
    try:
        conn = create_connection()
        c = conn.cursor()
        columns_str = ', '.join(columns)
        condition_str = ' AND '.join([f"{k} = %s" for k in condition])
        c.execute(f"SELECT {columns_str} FROM {table_name} WHERE {condition_str}", list(condition.values()))
        return c.fetchall()
    except psycopg2.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()


def add_new_group(group_id, pushup_goal, punishment, timezone):
    table_name = GROUPS_TABLE
    data = {
        'group_id': group_id,  # Manually specified group_id
        'pushup_goal': pushup_goal,
        'punishment': punishment,
        'timezone': timezone  # Include timezone information
    }

    create_row(table_name, data)


def change_group_timezone(group_id, new_timezone):
    table_name = GROUPS_TABLE
    update_data = {
        'timezone': new_timezone
    }
    update_condition = {
        'group_id': group_id
    }

    set_value(table_name, update_data, update_condition)


def get_timezone_automatically():
    try:
        local_timezone = pytz.timezone('Etc/GMT')
        local_timezone_name = datetime.now(local_timezone).astimezone().tzname()
        return local_timezone_name
    except Exception as e:
        print(f"Error while getting local timezone: {e}")
        return None

def add_new_user(telegram_id, group_id):
    table_name = USERS_TABLE
    data = {
        'telegram_id': telegram_id,
        'group_id': group_id
    }

    create_row(table_name, data)


def assign_user_to_group(telegram_id, group_id):
    update_data = {
        'group_id': group_id
    }
    update_condition = {
        'telegram_id': telegram_id
    }
    set_value(USERS_TABLE, update_data, update_condition)


def remove_user_from_group(telegram_id):
    assign_user_to_group(telegram_id, 0)

def update_pushups(telegram_id, pushups_count_increase):
    try:
        conn = create_connection()
        c = conn.cursor()

        # Fetch group_id and timezone offset for the user
        c.execute(f"SELECT g.timezone FROM {USERS_TABLE} u JOIN {GROUPS_TABLE} g ON u.group_id = g.group_id WHERE u.telegram_id = %s;", (telegram_id,))
        timezone_offset = c.fetchone()

        if timezone_offset:
            offset_hours = int(timezone_offset[0])
            current_utc_time = datetime.utcnow()
            current_local_time = current_utc_time + timedelta(hours=offset_hours)
            current_date = current_local_time.date().isoformat()
        else:
            print("User's group or timezone not found.")
            return

        # Check if a record exists for the current date
        c.execute(f"""
            SELECT pushups_count FROM {DAILY_PUSHUP_RECORD_TABLE}
            WHERE user_telegram_id = %s AND date = %s;
            """, (telegram_id, current_date))
        existing_record = c.fetchone()

        if existing_record:
            # Update the existing record
            new_pushups_count = existing_record[0] + pushups_count_increase
            c.execute(f"""
                UPDATE {DAILY_PUSHUP_RECORD_TABLE}
                SET pushups_count = %s
                WHERE user_telegram_id = %s AND date = %s;
                """, (new_pushups_count, telegram_id, current_date))
        else:
            # Insert a new record
            c.execute(f"""
                INSERT INTO {DAILY_PUSHUP_RECORD_TABLE} (user_telegram_id, date, pushups_count)
                VALUES (%s, %s, %s);
                """, (telegram_id, current_date, pushups_count_increase))

        conn.commit()
    except psycopg2.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()


#create_db()
#add_new_group(0, 100, 'A virtual group for non-group users')  # Manually specify group_id as 1
#add_new_group(123, 100, 'Fake group')
#assign_user_to_group(123456789, 123)
#create_db()
change_group_timezone(321, '-07')
#add_new_group(321, 50, "nothing", get_timezone_automatically())
#print(get_timezone_automatically())
#update_pushups(123456789, 9)
# Manually specify group_id as 1
#add_new_user(123456789, 0)
# delete_db()
# Example usage
# group_id = add_group(123, 50, "RM5 donation")
# add_user(123456789, group_id)
# set_data(USERS_TABLE, 123456789, GROUP_ID_COLUMN, 123, 123)
# print(get_data(USERS_TABLE, 'telegram_id', 'group_id', 123456789))
# print(get_users_in_group(group_id))

import os
from datetime import datetime, timedelta

import psycopg2
import pytz

from dotenv import load_dotenv
from psycopg2 import pool

# import pytz

# Load environment variables
load_dotenv("bot/.env")

# Database credentials
db_host = os.environ.get("PGHOST", "your_host")
db_user = os.environ.get("PGUSER", "your_user")
db_password = os.environ.get("PGPASSWORD", "your_password")
db_name = os.environ.get("PGDATABASE", "your_database")

# Database table names
USERS_TABLE = 'users'
GROUPS_TABLE = 'groups'
DAILY_PUSHUP_RECORD_TABLE = 'daily_pushup_record'


def create_db():
    with psycopg2.connect(host=db_host, user=db_user, password=db_password, database=db_name) as conn:
        c = conn.cursor()

        # Create Groups Table
        c.execute(f"""
            CREATE TABLE IF NOT EXISTS {GROUPS_TABLE} (
                group_id BIGINT PRIMARY KEY,  -- 'group_id' as Primary Key
                punishment TEXT,
                timezone TEXT,
                group_name TEXT
            );
        """)

        # Create Users Table
        c.execute(f"""
            CREATE TABLE IF NOT EXISTS {USERS_TABLE} (
                telegram_id BIGINT PRIMARY KEY,
                group_id BIGINT,
                language_text TEXT,
                joining_date DATE,
                timezone TEXT,
                pushup_goal INTEGER,
                FOREIGN KEY (group_id) REFERENCES {GROUPS_TABLE} (group_id)
            );
        """)

        # Create Daily Pushup Record Table
        c.execute(f"""
            CREATE TABLE IF NOT EXISTS {DAILY_PUSHUP_RECORD_TABLE} (
                user_telegram_id BIGINT,
                date DATE,
                pushups_count INTEGER,
                sets INTEGER,
                PRIMARY KEY (user_telegram_id, date),
                FOREIGN KEY (user_telegram_id) REFERENCES {USERS_TABLE} (telegram_id)
            );
        """)

        conn.commit()


def create_pool(minconn, maxconn, **kwargs):
    return psycopg2.pool.SimpleConnectionPool(minconn, maxconn, **kwargs)


pool = create_pool(minconn=1, maxconn=20, host=db_host, database=db_name, user=db_user, password=db_password)


# database design:
# Table: daily_pushup_record {
#     user_telegram_id (bigint)
#     date (date)
#     pushups_count (integer)
#     sets (integer)
# }
# Table: groups {
#     group_id (bigint)
#     punishment (text)
#     timezone (text)
#     group_name (text)
# }
# Table: users {
#     telegram_id (bigint)
#     group_id (bigint)
#     language_text (text)
#     joining_date (date)
#     timezone (text)
#     pushup_goal (integer)
# }
def set_value(table_name, data, condition):
    conn = pool.getconn()
    try:
        c = conn.cursor()
        update_str = ', '.join([f"{k} = %s" for k in data])
        condition_str = ' AND '.join([f"{k} = %s" for k in condition])
        c.execute(f"UPDATE {table_name} SET {update_str} WHERE {condition_str}",
                  list(data.values()) + list(condition.values()))
        conn.commit()
    except psycopg2.Error as e:
        print(f"Database error: {e}")
    finally:
        pool.putconn(conn)


def get_value(table_name, columns, condition):
    conn = pool.getconn()
    try:
        c = conn.cursor()
        columns_str = ', '.join(columns)
        condition_str = ' AND '.join([f"{k} = %s" for k in condition])
        c.execute(f"SELECT {columns_str} FROM {table_name} WHERE {condition_str}", list(condition.values()))
        return c.fetchall()
    except psycopg2.Error as e:
        print(f"Database error: {e}")
    finally:
        pool.putconn(conn)


def generate_database_design():
    with psycopg2.connect(host=db_host, user=db_user, password=db_password, database=db_name) as conn:
        c = conn.cursor()
        c.execute("""
            SELECT table_name, column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position;
        """)

        current_table = ''
        for row in c.fetchall():
            table_name, column_name, data_type = row
            if table_name != current_table:
                if current_table:
                    print('}')
                print(f'Table: {table_name} {{')
                current_table = table_name
            print(f'    {column_name} ({data_type})')
        print('}')


# def create_connection():
#     return psycopg2.connect(host=db_host, user=db_user, password=db_password, database=db_name)


def create_row(table_name, data):
    conn = pool.getconn()
    try:
        c = conn.cursor()
        columns = ', '.join(data.keys())
        values = ', '.join(['%s'] * len(data))
        c.execute(f"INSERT INTO {table_name} ({columns}) VALUES ({values})", list(data.values()))
        conn.commit()
    except psycopg2.Error as e:
        print(f"Database error: {e}")
    finally:
        pool.putconn(conn)


def delete_row(table_name, condition):
    conn = pool.getconn()
    try:
        c = conn.cursor()
        condition_str = ' AND '.join([f"{k} = %s" for k in condition])
        c.execute(f"DELETE FROM {table_name} WHERE {condition_str}", list(condition.values()))
        conn.commit()
    except psycopg2.Error as e:
        print(f"Database error: {e}")
    finally:
        pool.putconn(conn)


def add_new_group(group_id, pushup_goal, punishment, timezone, group_name):
    table_name = GROUPS_TABLE
    data = {
        'group_id': group_id,
        'pushup_goal': pushup_goal,
        'punishment': punishment,
        'timezone': timezone,
        'group_name': group_name
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


def get_group_timezone(group_id):
    table_name = GROUPS_TABLE
    columns = ['timezone']
    condition = {'group_id': group_id}

    result = get_value(table_name, columns, condition)

    if result:
        return result[0][0]  # Return the timezone value
    else:
        return None  # Return None if no matching group is found


def get_timezone_automatically():
    try:
        local_timezone = pytz.timezone('Etc/GMT')
        local_timezone_name = datetime.now(local_timezone).astimezone().tzname()
        return local_timezone_name
    except Exception as e:
        print(f"Error while getting local timezone: {e}")
        return None


def format_timezone(tz_str):
    """
    Format the timezone string to standard format.
    E.g., "+08" -> "UTC+08:00", "-01" -> "UTC-01:00"
    """
    # Check if the timezone string is in the expected format
    if len(tz_str) == 3 and tz_str[0] in ['+', '-'] and tz_str[1:].isdigit():
        return f"UTC{tz_str}:00"
    else:
        return "UTC+00:00"  # Default to UTC if the format is incorrect



def add_new_user(telegram_id, pushup_goal = 50, joining_date=None, timezone='+08', group_id=0):
    table_name = USERS_TABLE
    data = {
        'telegram_id': telegram_id,
        'group_id': group_id,
        'language_text': "English", # for now
        'joining_date': joining_date if joining_date else datetime.now(pytz.timezone(timezone)).date(), # you may change it to UTC +8 or else..
        'timezone': timezone,
        'pushup_goal': pushup_goal
    }

    create_row(table_name, data)


def check_user_exists(telegram_id):
    result = get_value(USERS_TABLE, ['COUNT(*)'], {'telegram_id': telegram_id})
    user_count = result[0][0] if result else 0
    return user_count > 0


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


# for testing
def create_pushups(telegram_id, pushups_count_increase, timezone_offset="+08"):
    conn = pool.getconn()
    try:
        c = conn.cursor()

        if timezone_offset:
            offset_hours = int(timezone_offset)
            current_utc_time = datetime.utcnow()
            current_local_time = current_utc_time + timedelta(hours=offset_hours)
            current_date = current_local_time.date().isoformat()
        else:
            print("User's group or timezone not found.")
            return

        # Check if a record exists for the current date
        c.execute(f"""
            SELECT pushups_count, sets FROM {DAILY_PUSHUP_RECORD_TABLE}
            WHERE user_telegram_id = %s AND date = %s;
            """, (telegram_id, current_date))
        existing_record = c.fetchone()

        if existing_record:
            # Update the existing record
            new_pushups_count = existing_record[0] + pushups_count_increase
            new_sets = existing_record[1] + 1
            c.execute(f"""
                UPDATE {DAILY_PUSHUP_RECORD_TABLE}
                SET pushups_count = %s, sets = %s
                WHERE user_telegram_id = %s AND date = %s;
                """, (new_pushups_count, new_sets, telegram_id, current_date))
        else:
            # Insert a new record with 1 set since it's the first entry of the day
            c.execute(f"""
                INSERT INTO {DAILY_PUSHUP_RECORD_TABLE} (user_telegram_id, date, pushups_count, sets)
                VALUES (%s, %s, %s, 1);
                """, (telegram_id, current_date, pushups_count_increase))

        conn.commit()
    except psycopg2.Error as e:
        print(f"Database error: {e}")
    finally:
        pool.putconn(conn)


def get_pushup_count(user_id, date):
    result = get_value(DAILY_PUSHUP_RECORD_TABLE, ['pushups_count'], {'user_telegram_id': user_id, 'date': date})
    return result[0][0] if result else 0


def update_user_language(telegram_id, new_language_text):
    set_value(USERS_TABLE, {'language_text': new_language_text}, {'telegram_id': telegram_id})


def update_group_language(telegram_id, new_language_text):
    set_value(GROUPS_TABLE, {'language_text': new_language_text}, {'telegram_id': telegram_id})


def get_user_language(telegram_id):
    result = get_value(USERS_TABLE, ['language_text'], {'telegram_id': telegram_id})
    return result[0][0] if result else None


# carry on here

def get_group_language(telegram_id):
    result = get_value(GROUPS_TABLE, ['language_text'], {'telegram_id': telegram_id})
    return result[0][0] if result else None


def get_date_by_timezone(timezone_offset="+08"):
    try:
        offset_hours = int(timezone_offset)
        current_utc_time = datetime.utcnow()
        current_local_time = current_utc_time + timedelta(hours=offset_hours)
        current_date = current_local_time.date().isoformat()
        return current_date
    except ValueError:
        # Handle invalid timezone offset gracefully, e.g., return None or raise an exception
        return None


def is_group_registered(group_id):
    """Check if the given group is registered in the database."""
    result = get_value(GROUPS_TABLE, ['telegram_id'], {'telegram_id': group_id})
    return bool(result)


def check_user_group_status(user_id, group_id):
    """Check the user's group status relative to the given group_id."""
    user_info = get_value(USERS_TABLE, ['group_id'], {'telegram_id': user_id})
    if user_info:
        assigned_group_id = user_info[0][0]
        if assigned_group_id == group_id:
            return 'same_group'
        else:
            return 'different_group'
    else:
        return 'no_group'


def assign_user_to_group(user_id, group_id):
    if get_value(USERS_TABLE, ['telegram_id'], {'telegram_id': user_id}):
        set_value(USERS_TABLE, {'group_id': group_id}, {'telegram_id': user_id})
    else:
        conn = pool.getconn()
        try:
            c = conn.cursor()
            c.execute(f"INSERT INTO {USERS_TABLE} (telegram_id, group_id) VALUES (%s, %s)", (user_id, group_id))
            conn.commit()
        except psycopg2.Error as e:
            print(f"Database error: {e}")
        finally:
            pool.putconn(conn)


def get_group_timezone(group_id):
    """Retrieve the timezone of the given group from the database."""
    result = get_value(GROUPS_TABLE, ['timezone'], {'telegram_id': group_id})
    if result:
        return result[0][0]
    else:
        return None
def check_group_registration(group_id):
    result = get_value(GROUPS_TABLE, ['COUNT(1)'], {'telegram_id': group_id})
    return result[0][0] > 0 if result else False


def set_pushup_count(group_id, pushup_count):
    set_value(GROUPS_TABLE, {'pushup_goal': pushup_count}, {'telegram_id': group_id})


def set_group_timezone(group_id, timezone):
    set_value(GROUPS_TABLE, {'timezone': timezone}, {'telegram_id': group_id})


# def remaining_pushups(telegram_id, date):
#     """
#     Calculate the remaining pushups for a user on a specific date.
#     """
#     conn = create_connection()
#     try:
#         with conn.cursor() as cur:
#             # Assuming pushup_goal is stored in the groups table
#             cur.execute(
#                 "SELECT pushup_goal FROM groups WHERE group_id = (SELECT group_id FROM users WHERE telegram_id = %s)",
#                 (telegram_id,))
#             pushup_goal = cur.fetchone()[0]
#
#             cur.execute("SELECT SUM(pushups_count) FROM daily_pushup_record WHERE user_telegram_id = %s AND date = %s",
#                         (telegram_id, date))
#             done_today = cur.fetchone()[0] or 0
#
#             return max(pushup_goal - done_today, 0)
#     finally:
#         conn.close()

from datetime import datetime, timedelta


# def calculate_remaining_pushups(telegram_id):
#     """
#     Calculate the remaining pushups for a user for the current date based on their timezone and goal in the users table.
#     """
#     conn = create_connection()
#     try:
#         with conn.cursor() as cur:
#             # Get the user's pushup goal and timezone from the users table
#             cur.execute(
#                 "SELECT pushup_goal, timezone FROM users WHERE telegram_id = %s",
#                 (telegram_id,))
#             result = cur.fetchone()
#             if not result:
#                 print("User not found")
#                 return None
#
#             pushup_goal, timezone = result
#             timezone_offset = int(timezone)
#             current_date = (datetime.utcnow() + timedelta(hours=timezone_offset)).date()
#
#             # Calculate done pushups for the current date
#             cur.execute("SELECT SUM(pushups_count) FROM daily_pushup_record WHERE user_telegram_id = %s AND date = %s",
#                         (telegram_id, current_date))
#             done_today = cur.fetchone()[0] or 0
#
#             return max(pushup_goal - done_today, 0)
#     finally:
#         conn.close()
#

def done_pushups(telegram_id, date=get_date_by_timezone()):
    result = get_value(DAILY_PUSHUP_RECORD_TABLE, ['SUM(pushups_count)'],
                       {'user_telegram_id': telegram_id, 'date': date})

    return result[0][0] if result and result[0] and result[0][0] is not None else 0


def set_pushup_goal(telegram_id, pushup_goal):
    """
    Set the pushup goal for a user.
    :param telegram_id: Telegram ID of the user.
    :param pushup_goal: Pushup goal to set.
    """
    set_value("users", {"pushup_goal": pushup_goal}, {"telegram_id": telegram_id})


def get_pushup_goal(telegram_id):
    """
    Get the pushup goal for a user.
    :param telegram_id: Telegram ID of the user.
    :return: Pushup goal of the user.
    """
    result = get_value("users", ["pushup_goal"], {"telegram_id": telegram_id})
    return result[0][0] if result else None


# not tested
def count_strike_missed_days(telegram_id):
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT g.timezone FROM groups g
                JOIN users u ON g.group_id = u.group_id
                WHERE u.telegram_id = %s
                """, (telegram_id,))
            result = cur.fetchone()
            if not result:
                print("User or group not found")
                return 0

            group_timezone = result[0]
            timezone_offset = int(group_timezone)
            current_date = (datetime.utcnow() + timedelta(hours=timezone_offset)).date()

            streak_count = 0
            for day in range(365):  # Check up to a year
                check_date = current_date - timedelta(days=day)
                cur.execute("""
                    SELECT 1 FROM daily_pushup_record
                    WHERE user_telegram_id = %s AND date = %s
                    """, (telegram_id, check_date))
                record_exists = cur.fetchone()

                if not record_exists:
                    streak_count += 1
                else:
                    break  # Found a day with pushups

            return streak_count
    finally:
        pool.putconn(conn)


# not tested
def count_strike_done_days(telegram_id):
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            # Get the user's pushup goal and timezone
            cur.execute("""
                SELECT g.pushup_goal, g.timezone FROM groups g
                JOIN users u ON g.group_id = u.group_id
                WHERE u.telegram_id = %s
                """, (telegram_id,))
            result = cur.fetchone()
            if not result:
                print("User or group not found")
                return 0

            pushup_goal, group_timezone = result
            timezone_offset = int(group_timezone)
            current_date = (datetime.utcnow() + timedelta(hours=timezone_offset)).date()

            streak_count = 0
            for day in range(365):  # Check up to a year
                check_date = current_date - timedelta(days=day)
                cur.execute("""
                    SELECT pushups_count FROM daily_pushup_record
                    WHERE user_telegram_id = %s AND date = %s
                    """, (telegram_id, check_date))
                pushups_count = cur.fetchone()

                if check_date == current_date and not pushups_count:
                    continue  # Don't break streak if today's record is missing

                if pushups_count and pushups_count[0] >= pushup_goal:
                    streak_count += 1
                else:
                    break  # Day missed or goal not met

            return streak_count
    finally:
        pool.putconn(conn)


def user_state(telegram_id):
    """
    Determine the state of the user - new, strikes, or regular.
    """
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            # Check if new user
            cur.execute("SELECT COUNT(1) FROM daily_pushup_record WHERE user_telegram_id = %s", (telegram_id,))
            if cur.fetchone()[0] == 0:
                return "New User"

            # Calculate strike missed and done days
            strike_missed_days = count_strike_missed_days(telegram_id)
            strike_done_days = count_strike_done_days(telegram_id)

            # Define a regular user based on your criteria
            if strike_missed_days > 1 or strike_done_days < 3:
                return f"User with Strikes - Missed: {strike_missed_days}, Done: {strike_done_days}"
            else:
                return f"Regular User - Done: {strike_done_days}, Missed: {strike_missed_days}"
    finally:
        pool.putconn(conn)


def is_new_user(user_id):
    result = get_value(DAILY_PUSHUP_RECORD_TABLE, ['COUNT(1)'], {'user_telegram_id': user_id})
    return result[0][0] == 0 if result else False


def get_remaining_pushups_user(telegram_id):
    # Get user's timezone
    user_timezone_result = get_value(USERS_TABLE, ['timezone'], {'telegram_id': telegram_id})
    if not user_timezone_result:
        print("User timezone not found.")
        return None
    user_timezone_str = user_timezone_result[0][0]

    # Convert the timezone format "+08" to a pytz timezone
    hours_offset = int(user_timezone_str[:3])
    tz_delta = timedelta(hours=hours_offset)
    user_timezone = datetime.now(pytz.utc).astimezone(pytz.utc) + tz_delta

    # Determine today's date based on user's timezone
    today = user_timezone.date()

    # Get user's pushup goal
    user_goal_result = get_value(USERS_TABLE, ['pushup_goal'], {'telegram_id': telegram_id})
    if not user_goal_result:
        print("User not found or error in fetching user goal.")
        return None
    user_goal = user_goal_result[0][0]

    # Get total pushups done by the user for today
    user_done_result = get_value(DAILY_PUSHUP_RECORD_TABLE, ['COALESCE(SUM(pushups_count), 0)'],
                                 {'user_telegram_id': telegram_id, 'date': today})
    if user_done_result is None:
        print("Error in fetching user's pushup count.")
        return None

    user_done = user_done_result[0][0]

    # Calculate remaining pushups
    remaining_pushups = user_goal - user_done
    return remaining_pushups


# def get_pushup_count_goal(user_id):
#     # Fetch the pushup goal for the given user_id
#     pushup_goal = get_value(USERS_TABLE, ['pushup_goal'], {'telegram_id': user_id})
#
#     if pushup_goal:
#         return pushup_goal[0][0]  # Return the first element of the first row if exists
#     else:
#         # Return a default value or handle the case when the user is not found
#         return None  # You can modify this as needed


# create a funcion that gets some data from database and calculate the latency
import time


def fetch_data_and_calculate_latency(table_name, columns):
    """
    Fetches data from a specified table and measures the latency.
    """
    print("starting database reqest now")
    start_time = time.time()  # Start time before the database operation

    # Performing the database operation
    data = check_user_exists(732496348)  # get_pushup_count_goal(732496348)

    end_time = time.time()  # End time after the database operation

    latency = end_time - start_time  # Calculate latency

    return data, latency


def fetch_user_pushup_data():
    users_pushup_data = []
    try:
        conn = pool.getconn()
        c = conn.cursor()

        # Fetch all users with their pushup goals
        c.execute("SELECT telegram_id, pushup_goal FROM users")
        users = c.fetchall()

        today_date = datetime.now(pytz.timezone('UTC')).astimezone(pytz.timezone('Asia/Singapore')).date()

        for user in users:
            user_id, pushup_goal = user

            # Fetch today's pushup count for the user
            c.execute(
                "SELECT COALESCE(SUM(pushups_count), 0) FROM daily_pushup_record WHERE user_telegram_id = %s AND date = %s",
                (user_id, today_date))
            done_pushups = c.fetchone()[0]

            # Calculate remaining pushups
            remaining_pushups = max(0, pushup_goal - done_pushups)

            users_pushup_data.append((user_id, done_pushups, remaining_pushups))

        conn.commit()
        return users_pushup_data
    except Exception as e:
        print(f"Database error: {str(e)}")
        return []
    finally:
        pool.putconn(conn)

#print(is_new_user(1823406139))
# def fetch_users_by_timezone(timezone):
#     # Get list of users, their done pushups and pushup goal based on timezone
#     user_condition = {'timezone': timezone}
#     user_columns = ['telegram_id', 'pushup_goal']
#     user_data = get_value('users', user_columns, user_condition)
#
#     # Prepare user data dict
#     users_info = {user[0]: {'goal': user[1]} for user in user_data}
#
#     # Fetch done pushups data for each user
#     for user_id in users_info.keys():
#         pushup_condition = {'user_telegram_id': user_id}
#         pushup_columns = ['pushups_count']
#         pushup_data = get_value('daily_pushup_record', pushup_columns, pushup_condition)
#         done_pushups = sum(pushup[0] for pushup in pushup_data)
#         users_info[user_id]['done'] = done_pushups
#
#     return users_info
#
# def prepare_user_info(users_info):
#     info_strings = []   # List to store user info strings
#
#     # Iterate over all users and prepare their pushup information
#     for telegram_id, pushup_info in users_info.items():
#         done_pushups = pushup_info['done']
#         goal_pushups = pushup_info['goal']
#         remaining_pushups = max(0, goal_pushups - done_pushups)
#         user_name = telegram_id  # Here you need to retrieve the user name based on telegram_id
#         # Append user info string to the list
#         info_strings.append(f'User: {user_name}\nDone: {done_pushups}\nGoal: {goal_pushups}\nRemaining: {remaining_pushups}')
#
#     # Join all info strings with a separator and return
#     return '\n\n'.join(info_strings)
#
# users_info = fetch_users_by_timezone('+08')
# print(prepare_user_info(users_info))

# data, latency = fetch_data_and_calculate_latency(DAILY_PUSHUP_RECORD_TABLE, ['telegram_id', 'date'])

# print(f"Fetched data: {data} | latency: {latency}")
# create_db()
# generate_database_design()
# print(get_remaining_pushups_user(732496348))
# print(get_pushup_goal(732496348))
# print(get_remaining_pushups_user(123456789))
# generate_database_design()
# create_pushups(123456789, 15, "-08")
# create_pushups(123456789, 15, "-28")
# print(count_strike_done_days(123456789))
# print(user_state(123456789))
# generate_database_design()

# Provide the user_id and date in 'YYYY-MM-DD' format
# user_id = 123456789
# #date = '2023-12-28'
#
# # Provide the timezone offset as a string or integer
# timezone_offset = "+06"  # or timezone_offset = -1
#
# # Call the get_date_by_timezone function
# date_in_timezone = get_date_by_timezone(timezone_offset)
#
# if date_in_timezone is not None:
#     print(f"Date in timezone {timezone_offset}: {date_in_timezone}")
# else:
#     print("Invalid timezone offset.")
#
# create_pushups(user_id, 69, timezone_offset)
# # Call the get_pushup_count function to retrieve the pushup count
# pushup_count = get_pushup_count(user_id, get_date_by_timezone(timezone_offset))
#
#
# # Display the result
# print(f"Pushup count for user {user_id} on {date_in_timezone}: {pushup_count}")
# upgrade_id_columns_to_bigint(db_host, db_user, db_password, db_name, GROUPS_TABLE, USERS_TABLE, DAILY_PUSHUP_RECORD_TABLE)
# generate_database_design()
# add_new_group(-1002127852426, 100 ,'Pay RM10', '+08', '100 Pushups or -RM10')
# create_db()
# add_new_group(0, 100, 'A virtual group for non-group users')  # Manually specify group_id as 1
# add_new_group(123, 100, 'Fake group')
# assign_user_to_group(123456789, 123)
# create_db()
# add_new_group(-1002127852426, 100, "Pay RM10", get_timezone_automatically())
# change_group_timezone(321, get_timezone_automatically())
# create_pushups(2012089704, 50, -20)
# add_new_group('-1002127852426')

# Sadman 2012089704
# create_pushups(123456789, 100, '+1')
# change_group_timezone(321, '-07')
# add_new_group(321, 50, "nothing", get_timezone_automatically())
# print(get_timezone_automatically())
# update_pushups(123456789, 9)
# Manually specify group_id as 1
# add_new_user(123456789, 0)
# delete_db()
# Example usage
# group_id = add_group(123, 50, "RM5 donation")
# add_user(123456789, group_id)
# set_data(USERS_TABLE, 123456789, GROUP_ID_COLUMN, 123, 123)
# print(get_data(USERS_TABLE, 'telegram_id', 'group_id', 123456789))
# print(get_users_in_group(group_id))

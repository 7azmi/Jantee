import os
from fastapi import FastAPI, HTTPException
import psycopg2
import uvicorn
from datetime import timedelta, datetime
#import pytz

# Database credentials
db_host = os.environ.get("PGHOST", "your_host")
db_user = os.environ.get("PGUSER", "your_user")
db_password = os.environ.get("PGPASSWORD", "your_password")
db_name = os.environ.get("PGDATABASE", "your_database")
db_port = os.environ.get("PGPORT", "your_database")

app = FastAPI()
connection = psycopg2.connect(
    host=db_host,
    port=db_port,
    database=db_name,
    user=db_user,
    password=db_password
)


@app.get('/api/users')
def get_users():
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM users")
    items = cursor.fetchall()
    cursor.close()
    return items


@app.get('/api/groups')
def get_groups():
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM groups")
    items = cursor.fetchall()
    cursor.close()
    return items


@app.get('/api/users/{telegram_id}')
def get_user_by_telegram_id(telegram_id: int):
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM users WHERE telegram_id = %s", (telegram_id,))
    item = cursor.fetchone()
    cursor.close()
    if item:
        return item
    else:
        raise HTTPException(status_code=404, detail="User not found")


@app.get('/api/pushups/done_today/{telegram_id}')
def pushups_done_today(telegram_id: int):
    current_date = datetime.date.today()
    cursor = connection.cursor()
    query = "SELECT pushups_count FROM daily_pushup_record WHERE user_telegram_id = %s AND date = %s"
    cursor.execute(query, (telegram_id, current_date))
    result = cursor.fetchone()
    cursor.close()
    return {'pushups_done_today': result[0] if result else 0}


@app.get('/api/pushups/remaining_today/{telegram_id}')
def remaining_pushups_today(telegram_id: int):
    current_date = datetime.date.today()
    cursor = connection.cursor()
    cursor.execute("SELECT g.pushup_goal, COALESCE(p.pushups_count, 0) FROM groups g JOIN users u ON g.group_id = u.group_id LEFT JOIN daily_pushup_record p ON u.telegram_id = p.user_telegram_id AND p.date = %s WHERE u.telegram_id = %s", (current_date, telegram_id))
    result = cursor.fetchone()
    cursor.close()
    if result:
        remaining = max(result[0] - result[1], 0)
        return {'remaining_pushups_today': remaining}
    else:
        raise HTTPException(status_code=404, detail="User or group not found")


@app.get('/api/user/group_name/{telegram_id}')
def get_user_group_name(telegram_id: int):
    cursor = connection.cursor()
    query = "SELECT g.group_name FROM groups g JOIN users u ON g.group_id = u.group_id WHERE u.telegram_id = %s"
    cursor.execute(query, (telegram_id,))
    result = cursor.fetchone()
    cursor.close()
    return {'group_name': result[0] if result else 'No group found'}


@app.get('/api/pushups/streak/{telegram_id}')
def pushup_streak(telegram_id: int):
    # Get UTC now, to be adjusted according to the group's timezone
    utc_now = datetime.utcnow()

    cursor = connection.cursor()

    # Get the user's pushup goal and timezone
    cursor.execute(
        "SELECT g.pushup_goal, g.timezone FROM groups g JOIN users u ON g.group_id = u.group_id WHERE u.telegram_id = %s",
        (telegram_id,))
    result = cursor.fetchone()
    if not result:
        cursor.close()
        raise HTTPException(status_code=404, detail="User or group not found")

    pushup_goal, group_timezone = result

    # Adjust current date to group's timezone
    timezone_offset = int(group_timezone)
    current_date = (utc_now + timedelta(hours=timezone_offset)).date()

    # Initialize streak count
    streak_count = 0

    for day in range(0, 365):  # Assuming to check up to a year backwards
        check_date = current_date - timedelta(days=day)
        cursor.execute("SELECT pushups_count FROM daily_pushup_record WHERE user_telegram_id = %s AND date = %s",
                       (telegram_id, check_date))
        result = cursor.fetchone()

        # If it's today and there's no record yet, don't break the streak
        if check_date == current_date and not result:
            continue

        # If there's a record and it meets or exceeds the goal, increment the streak
        if result and result[0] >= pushup_goal:
            streak_count += 1
        else:
            # If a day is missed or doesn't meet the goal, break the streak
            break

    cursor.close()
    return {'pushup_streak': streak_count}


@app.get('/api/pushups/total/{telegram_id}')
def total_pushups_done(telegram_id: int):
    cursor = connection.cursor()
    query = "SELECT SUM(pushups_count) FROM daily_pushup_record WHERE user_telegram_id = %s"
    cursor.execute(query, (telegram_id,))
    result = cursor.fetchone()
    cursor.close()
    return {'total_pushups_done': result[0] if result and result[0] is not None else 0}


@app.get('/api/pushups/missed_days/{telegram_id}')
def missed_days_this_month(telegram_id: int):
    current_month = datetime.date.today().replace(day=1)
    cursor = connection.cursor()
    cursor.execute("SELECT g.pushup_goal FROM groups g JOIN users u ON g.group_id = u.group_id WHERE u.telegram_id = %s", (telegram_id,))
    pushup_goal = cursor.fetchone()
    if pushup_goal:
        pushup_goal = pushup_goal[0]
        query = "SELECT COUNT(*) FROM generate_series(%s, CURRENT_DATE, '1 day'::interval) AS calendar WHERE NOT EXISTS (SELECT 1 FROM daily_pushup_record WHERE user_telegram_id = %s AND date = calendar AND pushups_count >= %s)"
        cursor.execute(query, (current_month, telegram_id, pushup_goal))
        missed_days = cursor.fetchone()[0]
        cursor.close()
        return {'missed_days_this_month': missed_days}
    else:
        cursor.close()
        raise HTTPException(status_code=404, detail="User or group not found")


#def run_API():
#uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("API_PORT", 5000)))

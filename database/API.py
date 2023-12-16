import datetime
import os
import psycopg2
from flask import Flask, jsonify, request

# Database credentials
db_host = os.environ.get("PGHOST", "your_host")
db_user = os.environ.get("PGUSER", "your_user")
db_password = os.environ.get("PGPASSWORD", "your_password")
db_name = os.environ.get("PGDATABASE", "your_database")
db_port = os.environ.get("PGPORT", "your_database")

app = Flask(__name__)
connection = psycopg2.connect(
    host=db_host,
    port=db_port,
    database=db_name,
    user=db_user,
    password=db_password
)


@app.route('/api/users', methods=['GET'])
def get_items():
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM users")
    items = cursor.fetchall()
    cursor.close()
    return jsonify(items), 200


@app.route('/api/groups', methods=['GET'])
def get_groups():
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM groups")
    items = cursor.fetchall()
    cursor.close()
    return jsonify(items), 200


@app.route('/api/users/<int:telegram_id>', methods=['GET'])
def get_user_by_telegram_id(telegram_id):
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM users WHERE telegram_id = %s", (telegram_id,))
    item = cursor.fetchone()
    cursor.close()
    return jsonify(item), 200 if item else (jsonify({"error": "User not found"}), 404)

@app.route('/api/pushups/done_today/<int:telegram_id>', methods=['GET'])
def pushups_done_today(telegram_id):
    current_date = datetime.date.today()
    cursor = connection.cursor()
    query = "SELECT pushups_count FROM daily_pushup_record WHERE user_telegram_id = %s AND date = %s"
    cursor.execute(query, (telegram_id, current_date))
    result = cursor.fetchone()
    cursor.close()
    return jsonify({'pushups_done_today': result[0] if result else 0}), 200


@app.route('/api/pushups/remaining_today/<int:telegram_id>', methods=['GET'])
def remaining_pushups_today(telegram_id):
    current_date = datetime.date.today()
    cursor = connection.cursor()
    cursor.execute("SELECT g.pushup_goal, COALESCE(p.pushups_count, 0) FROM groups g JOIN users u ON g.group_id = u.group_id LEFT JOIN daily_pushup_record p ON u.telegram_id = p.user_telegram_id AND p.date = %s WHERE u.telegram_id = %s", (current_date, telegram_id))
    result = cursor.fetchone()
    cursor.close()
    if result:
        remaining = max(result[0] - result[1], 0)
        return jsonify({'remaining_pushups_today': remaining}), 200
    else:
        return jsonify({'error': 'User or group not found'}), 404


@app.route('/api/user/group_name/<int:telegram_id>', methods=['GET'])
def get_user_group_name(telegram_id):
    cursor = connection.cursor()
    query = "SELECT g.group_name FROM groups g JOIN users u ON g.group_id = u.group_id WHERE u.telegram_id = %s"
    cursor.execute(query, (telegram_id,))
    result = cursor.fetchone()
    cursor.close()
    return jsonify({'group_name': result[0] if result else 'No group found'}), 200


@app.route('/api/pushups/total/<int:telegram_id>', methods=['GET'])
def total_pushups_done(telegram_id):
    cursor = connection.cursor()
    query = "SELECT SUM(pushups_count) FROM daily_pushup_record WHERE user_telegram_id = %s"
    cursor.execute(query, (telegram_id,))
    result = cursor.fetchone()
    cursor.close()
    return jsonify({'total_pushups_done': result[0] if result and result[0] is not None else 0}), 200


@app.route('/api/pushups/missed_days/<int:telegram_id>', methods=['GET'])
def missed_days_this_month(telegram_id):
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
        return jsonify({'missed_days_this_month': missed_days}), 200
    else:
        cursor.close()
        return jsonify({'error': 'User or group not found'}), 404

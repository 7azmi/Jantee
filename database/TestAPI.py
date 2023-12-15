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


app.run(debug=True)
from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime


app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('sensor_data.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return 'Sensor data server is running!'

@app.route('/data', methods=['POST'])
def receive_data():
    try:
        data = request.get_json()
        temp_outside = data['sensor1']
        temp_back = data['sensor2']
        temp_come = data['sensor3']
        temp_inside = data['sensor4']
        gas = data['gas']
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print("Получены данные:")
        print("T1 (outside):", temp_outside)
        print("T2 (back):", temp_back)
        print("T3 (come):", temp_come)
        print("T4 (inside):", temp_inside)
        print("Gas:", gas)
        print("Timestamp:", timestamp)

        conn = get_db_connection()
        conn.execute('''
            INSERT INTO sensor_data (temp_outside, temp_back, temp_come, temp_inside, gas, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (temp_outside, temp_back, temp_come, temp_inside, gas, timestamp))
        conn.commit()
        conn.close()

        return jsonify({'message': 'Data received successfully'}), 200
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@app.route('/latest', methods=['GET'])
def latest_data():
    conn = get_db_connection()
    row = conn.execute('SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT 1').fetchone()
    conn.close()
    if row:
        return jsonify({
            "temp_outside": row["temp_outside"],
            "temp_back": row["temp_back"],
            "temp_come": row["temp_come"],
            "temp_inside": row["temp_inside"],
            "gas": row["gas"],
            "timestamp": row["timestamp"]
        })
    else:
        return jsonify({"message": "Нет данных"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
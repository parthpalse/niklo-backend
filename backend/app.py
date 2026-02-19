from flask import Flask, jsonify, request
from config import Config
from services.traffic_service import TrafficService

app = Flask(__name__)
app.config.from_object(Config)

traffic_service = TrafficService()

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'NikLo Backend'}), 200

@app.route('/api/traffic', methods=['POST'])
def get_traffic():
    data = request.json
    origin = data.get('origin')
    destination = data.get('destination')
    
    if not origin or not destination:
        return jsonify({'error': 'Origin and Destination are required'}), 400

    result = traffic_service.get_travel_time(origin, destination)
    
    if 'error' in result:
        return jsonify(result), 500
        
    return jsonify(result), 200

from services.commute_service import CommuteService
commute_service = CommuteService()

@app.route('/api/commute', methods=['POST'])
def get_commute_plan():
    data = request.json
    origin = data.get('origin')
    destination = data.get('destination')
    arrival_time = data.get('arrival_time') # Format HH:MM
    
    if not all([origin, destination, arrival_time]):
         return jsonify({'error': 'Missing fields'}), 400
         
    try:
        plan = commute_service.calculate_best_route(origin, destination, arrival_time)
        return jsonify(plan), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Advanced Features
from services.notification_service import NotificationService
from services.ml_service import MLService

notification_service = NotificationService()
ml_service = MLService()

@app.route('/api/notify', methods=['POST'])
def send_notification():
    data = request.json
    token = data.get('token')
    title = data.get('title')
    body = data.get('body')
    
    if not all([token, title, body]):
        return jsonify({'error': 'Missing fields'}), 400
        
    result = notification_service.send_push_notification(token, title, body)
    return jsonify(result), 200

@app.route('/api/predict', methods=['POST'])
def predict_commute():
    data = request.json
    time_str = data.get('time') # HH:MM
    day = data.get('day_of_week') # 0=Mon, 6=Sun
    
    if not time_str or day is None:
        return jsonify({'error': 'Missing fields'}), 400
        
    try:
        dt = datetime.strptime(time_str, '%H:%M')
        prediction = ml_service.predict_commute_time(dt.hour, dt.minute, day)
        return jsonify({'predicted_duration_mins': prediction}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

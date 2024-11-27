# backend/app.py

from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/api/echo', methods=['POST'])
def echo_username():
    data = request.get_json()
    if not data or 'username' not in data:
        return jsonify({'error': 'No username provided'}), 400
    
    username = data['username']
    return jsonify({'username': username}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

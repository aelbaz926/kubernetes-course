from flask import Flask
import time
import random

app = Flask(__name__)
is_ready = True
start_time = time.time()
request_count = 0

@app.route('/health')
def health():
    # Liveness: Is the app process alive?
    return 'OK', 200

@app.route('/ready')
def ready():
    # Readiness: Can we serve traffic?
    if is_ready:
        return 'Ready', 200
    return 'Not ready - database unavailable', 503

@app.route('/toggle-ready')
def toggle_ready():
    global is_ready
    is_ready = not is_ready
    status = "ready" if is_ready else "not ready"
    return f'Application is now {status}', 200

@app.route('/')
def home():
    global request_count
    request_count += 1
    if not is_ready:
        return 'Service unavailable - database down', 503
    return {
        'status': 'healthy',
        'uptime': int(time.time() - start_time),
        'requests_served': request_count
    }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

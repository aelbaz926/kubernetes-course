from flask import Flask, request
import time

app = Flask(__name__)
is_healthy = True
start_time = time.time()

@app.route('/health')
def health():
    if is_healthy:
        return 'OK', 200
    return 'Unhealthy', 500

@app.route('/break')
def break_app():
    global is_healthy
    is_healthy = False
    return 'Application is now broken! Liveness probe will fail.', 200

@app.route('/fix')
def fix_app():
    global is_healthy
    is_healthy = True
    return 'Application fixed!', 200

@app.route('/')
def home():
    if not is_healthy:
        return 'Application is broken!', 500
    return f'App healthy! Uptime: {int(time.time() - start_time)}s'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

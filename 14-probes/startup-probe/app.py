from flask import Flask
import time
import os

app = Flask(__name__)
start_time = time.time()
STARTUP_DELAY = 30  # Simulates slow startup

@app.route('/startup')
def startup():
    elapsed = time.time() - start_time
    if elapsed < STARTUP_DELAY:
        return f'Still starting... {int(elapsed)}s/{STARTUP_DELAY}s', 503
    return 'Started!', 200

@app.route('/')
def home():
    return f'App running! Uptime: {int(time.time() - start_time)}s'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

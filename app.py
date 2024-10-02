from flask import Flask, redirect, url_for, session, render_template, Response, jsonify
from authlib.integrations.flask_client import OAuth
import cv2
import os
app = Flask(__name__)
app.secret_key = 'e54ca775-c3f5-4b31-beea-c95a10833af1'  # Change this to a random secret key
# Path to the log file
LOG_FILE = 'login_attempts.txt'
# Google OAuth setup
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id='',
    client_secret='',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',
    # This is only needed if using openId to fetch user info
    client_kwargs={'scope': 'openid email profile'},
    jwks_uri = "https://www.googleapis.com/oauth2/v3/certs"
)

ALLOWED_EMAILS = ['email@gmail.com', 'email@gmail.com']

# List of RTSP URLs for the cameras
camera_urls = [
    'rtsp://cam/live/channel',  # Camera 1 RTSP URL
    'rtsp://cam/live/channe2',  # Camera 2 RTSP URL
    'rtsp://cam/live/channe3',  # Camera 3 RTSP URL
    'rtsp://cam/live/channe4'   # Camera 4 RTSP URL
]


# Function to access the RTSP stream from a specific camera
def gen(camera_index):
    cap = cv2.VideoCapture(camera_urls[camera_index])

    if not cap.isOpened():  # If the feed is not available
        yield (b'--frame\r\n'
               b'Content-Type: text/html\r\n\r\n'
               b'<div style="color:white;text-align:center">'
               b'<h2>Feed not available</h2><br>'
               b'<button onclick="window.location.reload()">Refresh</button>'
               b'</div>\r\n')
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# Google OAuth routes
@app.route('/login')
def login():
    return google.authorize_redirect(redirect_uri=url_for('auth_callback', _external=True))

@app.route('/auth/callback')
def auth_callback():
    token = google.authorize_access_token()
    user_info = google.get('userinfo').json()

    # Log the attempted login
    log_login_attempt(user_info['email'])

    # Check if the user's email is in the allowed list
    if user_info['email'] not in ALLOWED_EMAILS:
        return "Access Denied: Your email is not authorized.", 403

    # Store user information in session
    session['user'] = user_info
    return redirect(url_for('index'))

def log_login_attempt(email):
    """Log the email of the user who attempted to log in."""
    with open(LOG_FILE, 'a') as f:
        f.write(f"{email}\n")  # Append the email to the log file

# Ensure the log file exists
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, 'w') as f:
        pass  # Create the file if it doesn't exist


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

# Main page showing all camera feeds (requires login)
@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

# Route to show the camera feed (requires login)
@app.route('/video_feed/<int:camera_index>')
def video_feed(camera_index):
    if 'user' not in session:  # Check if the user is logged in
        return redirect(url_for('login'))  # Redirect to login if not

    if camera_index >= len(camera_urls):
        return jsonify({"error": "Invalid camera index"}), 404
    return Response(gen(camera_index),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# ENTER PORT FOR YOUR NVR TCP HERE
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=37777)

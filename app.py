import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request, send_from_directory
from flask_socketio import SocketIO, emit
import random
import requests
import os

app = Flask(__name__)

# Ensure Flask serves static files correctly
app.config['STATIC_FOLDER'] = 'static'

socketio = SocketIO(app)

# Dictionary to store connected users
users = {}

def get_gender_from_name(name):
    """
    Determines gender based on the name using Genderize API.
    Returns 'male', 'female', or 'unknown' if the gender cannot be determined.
    """
    try:
        response = requests.get(f"https://api.genderize.io/?name={name}")
        if response.status_code == 200:
            gender_data = response.json()
            if "gender" in gender_data and gender_data["gender"]:
                return gender_data["gender"]
    except Exception as e:
        print("Gender API error:", e)
    
    return "unknown"  # Default to unknown if API call fails

@app.route('/')
def index():
    return render_template('index.html')

# Ensure static files (CSS & JS) are accessible
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(app.config['STATIC_FOLDER'], filename)

@socketio.on("connect")
def handle_connect():
    username = f"User_{random.randint(1000, 9999)}"

    # Get gender from name
    gender = get_gender_from_name(username)

    # Ensure gender is correctly mapped
    avatar_gender = "boy" if gender == "male" else "girl" if gender == "female" else "boy"

    # Assign avatar URL based on detected gender
    avatar_url = f"https://avatar.iran.liara.run/public/{avatar_gender}?username={username}"

    users[request.sid] = {"username": username, "avatar": avatar_url}

    emit("user_joined", {"username": username, "avatar": avatar_url}, broadcast=True)
    emit("set_username", {"username": username})

@socketio.on("disconnect")
def handle_disconnect():
    user = users.pop(request.sid, None)
    if user:
        emit("user_left", {"username": user["username"]}, broadcast=True)

@socketio.on("send_message")
def handle_message(data):
    user = users.get(request.sid)
    if user:
        emit("new_message", {
            "username": user["username"],
            "avatar": user["avatar"],
            "message": data["message"]
        }, broadcast=True)

@socketio.on("update_username")
def handle_update_username(data):
    old_username = users[request.sid]["username"]
    new_username = data["username"]

    # Get new gender and avatar based on updated username
    gender = get_gender_from_name(new_username)
    avatar_gender = "boy" if gender == "male" else "girl" if gender == "female" else "boy"
    avatar_url = f"https://avatar.iran.liara.run/public/{avatar_gender}?username={new_username}"

    users[request.sid] = {"username": new_username, "avatar": avatar_url}

    emit("username_updated", {
        "old_username": old_username,
        "new_username": new_username,
        "avatar": avatar_url
    }, broadcast=True)

if __name__ == "__main__":
    socketio.run(app)

import os
from dotenv import load_dotenv
from flask import Flask, render_template, send_from_directory, request, g, redirect
import sqlite3

from python.form_submission import formSubmission
from python.init_db import init_db

load_dotenv()
app = Flask(__name__)

DATABASE = 'database.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        init_db()
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.route("/")
def hello_world():
    return send_from_directory('static', 'Homepage.html')

@app.route("/TrackingRequest")
def trackingRequest():
    return send_from_directory('static', 'TrackingRequest.html')

@app.route("/SubmitTrackingRequest", methods=['POST'])
def submitTrackingRequest():

    form = formSubmission(
        latitude = request.form.get('target_coordinates_latitude'),
        longitude = request.form.get('target_coordinates_longitude'),
        track_period = request.form.get('track_period'),
        time_range = request.form.get('time_range'),
        cloud_cover = request.form.get('cloud_cover'),
        notification_frequency_15m = request.form.get('notification_frequency_15m'),
        email = request.form.get('email')
    )

    con = get_db()
    cur = con.cursor()
    cur.execute(f"""
        INSERT INTO requests (
                latitude,
                longitude,
                track_period,
                time_range,
                cloud_cover,
                notification_frequency_15m,
                email
        ) VALUES (
            {form.latitude},
            {form.longitude},
            "{form.track_period}",
            "{form.time_range}",
            {form.cloud_cover},
            {form.notification_frequency_15m},
            "{form.email}"
        );
    """)
    con.commit()

    return  redirect(f'/request/{cur.lastrowid}')

@app.route('/request/<request_id>')
def getRequest(request_id):
    con = get_db()
    cur = con.cursor()
    res = cur.execute(f"""SELECT * FROM requests WHERE id={request_id}""")
    return str(res.fetchone())

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
from datetime import datetime, timezone
import io
import os
from dotenv import load_dotenv
from flask import Flask, render_template, send_from_directory, request, g, redirect, Response
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import sqlite3


from python.form_submission import formSubmission
from python.init_db import init_db
from python.n2yo_api import landsat_passes
from python.landsat import landsat_catalog_search

load_dotenv()
app = Flask(__name__)

DATABASE = 'database.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        init_db()
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def get_request(request_id):
    con = get_db()
    cur = con.cursor()
    res = cur.execute(f"""SELECT * FROM requests WHERE id={request_id}""")
    row = cur.fetchone() # Query should only return one value
    return row

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
        time_range_start = request.form.get('time_range_start'),
        time_range_end = request.form.get('time_range_end'),
        cloud_cover = request.form.get('cloud_cover'),
        notification_frequency_15m = 1 if request.form.get('notification_frequency_15m') is not None else 0,
        notification_frequency_30m = 1 if request.form.get('notification_frequency_30m') is not None else 0,
        notification_frequency_1hr = 1 if request.form.get('notification_frequency_1hr') is not None else 0,
        notification_frequency_6hr = 1 if request.form.get('notification_frequency_6hr') is not None else 0,
        notification_frequency_12hr = 1 if request.form.get('notification_frequency_12hr') is not None else 0,
        notification_frequency_1d = 1 if request.form.get('notification_frequency_1d') is not None else 0,
        notification_frequency_1w = 1 if request.form.get('notification_frequency_1w') is not None else 0,
        email = request.form.get('contact_email')
    )

    con = get_db()
    cur = con.cursor()
    cur.execute(f"""
        INSERT INTO requests (
                latitude,
                longitude,
                track_period,
                time_range_start,
                time_range_end,
                cloud_cover,
                notification_frequency_15m,
                notification_frequency_15m,
                notification_frequency_30m,
                notification_frequency_1hr,
                notification_frequency_6hr,
                notification_frequency_12hr,
                notification_frequency_1d,
                notification_frequency_1w,
                email
        ) VALUES (
            {form.latitude},
            {form.longitude},
            "{form.track_period}",
            "{form.time_range_start}",
            "{form.time_range_end}",
            {form.cloud_cover},
            {form.notification_frequency_15m},
            {form.notification_frequency_15m},
            {form.notification_frequency_30m},
            {form.notification_frequency_1hr},
            {form.notification_frequency_6hr},
            {form.notification_frequency_12hr},
            {form.notification_frequency_1d},
            {form.notification_frequency_1w},
            "{form.email}"
        );
    """)
    con.commit()

    return  redirect(f'/request/{cur.lastrowid}')

@app.route('/request/<request_id>')
def getRequest(request_id):
    row = get_request(request_id)
    passes = landsat_passes(longitude=row['longitude'], latitude=row['latitude'])
    if len(passes) > 0:
        next_pass_time = passes[0]
    else:
        return 'Error'
    # Get LandSAT data if time has passed
    if next_pass_time < datetime.now(tz=timezone.utc):
        return render_template(
            'request_complete.html',
            next_pass_time=next_pass_time,
            request_id=request_id
        )
    else:
        return render_template(
            'request_pending.html',
            next_pass_time=next_pass_time,
            request_id=request_id
        )

@app.route('/landsat/<request_id>_rgb.png')
def generateLandsatRGB(request_id):
    con = get_db()
    cur = con.cursor()
    res = cur.execute(f"""SELECT * FROM requests WHERE id={request_id}""")
    row = cur.fetchone() # Query should only return one value
    fig = landsat_catalog_search(longitude=row['longitude'], latitude=row['latitude'])
    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    return Response(output.getvalue(), mimetype='image/png')

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
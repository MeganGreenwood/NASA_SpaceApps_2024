from datetime import datetime, timezone, timedelta
import glob
import io
import os
from dotenv import load_dotenv
from flask import Flask, render_template, send_from_directory, request, g, redirect, Response, url_for, send_file
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import sqlite3


from python.form_submission import formSubmission
from python.init_db import init_db
from python.n2yo_api import landsat_passes
from python.landsat import LandsatData
from python.gmail import send_pass_reminder

load_dotenv()
app = Flask(__name__)

DATABASE = 'database/database.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        init_db()
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def get_request(request_id) -> sqlite3.Row:
    con = get_db()
    cur = con.cursor()
    res = cur.execute(f"""SELECT * FROM requests WHERE id={request_id}""")
    row = cur.fetchone() # Query should only return one value
    return row

def get_remind_interval(row: sqlite3.Row) -> list[str, timedelta]:
    """
    Take in row of db and figure out which notification interval the user selected.
    Output is 2 lists, one is the interval in english, and the second is a timedelta object representing the interval
    """
    english_intervals = []
    deltas = []
    if row['notification_frequency_15m'] == 1:
        english_intervals.append('15 minutes')
        deltas.append(timedelta(minutes=15))
    if row['notification_frequency_30m'] == 1:
        english_intervals.append('30 minutes')
        deltas.append(timedelta(minutes=30))
    if row['notification_frequency_1hr'] == 1:
        english_intervals.append('1 hour')
        deltas.append(timedelta(hours=1))
    if row['notification_frequency_6hr'] == 1:
        english_intervals.append('6 hours')
        deltas.append(timedelta(hours=6))
    if row['notification_frequency_12hr'] == 1:
        english_intervals.append('12 hours')
        deltas.append(timedelta(hours=12))
    if row['notification_frequency_1d'] == 1:
        english_intervals.append('1 day')
        deltas.append(timedelta(days=1))
    if row['notification_frequency_1w'] == 1:
        english_intervals.append('1 week')
        deltas.append(timedelta(weeks=1))
    return english_intervals, deltas

def get_time_range_dt(row: sqlite3.Row):
    time_range_start = None
    if row['time_range_start'] != '':
        time_range_start = datetime.strptime(row['time_range_start']+'+0000', '%Y-%m-%d%z')
    time_range_end = None
    if row['time_range_end'] != '':
        time_range_end = datetime.strptime(row['time_range_end']+'+0000', '%Y-%m-%d%z')
    return time_range_start, time_range_end

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
        track_period = request.form.get('track_period_next'), # TODO this is just a true/false for a radio input
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
    time_range_start, time_range_end = get_time_range_dt(row)
    
    remind_intervals_names, remind_deltas = get_remind_interval(row)
    remind_delta_timestamps = [datetime.now(tz=timezone.utc) - delta for delta in remind_deltas]

    passes = landsat_passes(
        longitude=row['longitude'],
        latitude=row['latitude'],
        time_range_start=time_range_start,
        time_range_end=time_range_end
    )
    passes_str = [pass_dt.strftime('%Y-%m-%d_%H:%M:%S') for pass_dt in passes]
    if len(passes) > 0:
        next_pass_time = passes[0]
    else:
        return 'No Passes Found'
    # Get LandSAT data if time has passed
    # TODO: checking if range is less than today doesn't guarantee request is complete
    # TODO: Email is only sent at request creation time - not a fully functioning reminder system
    if next_pass_time < datetime.now(tz=timezone.utc) or (time_range_start or datetime(9999,1,1, tzinfo=timezone.utc)) < datetime.now(tz=timezone.utc):
        # TODO Record that we have sent email so users do not get emailed every time this page is refreshed
        try:
            send_pass_reminder(row['email'], next_pass_time, remind_intervals_names, request_id, 'https://landsatconnect.earth' + url_for('getRequest',request_id=request_id))
        except:
            print('Failed to send email')
        return render_template(
            'request_complete.html',
            request_id=request_id,
            request_passes=passes_str,
            latitude=row['latitude'],
            longitude=row['longitude']
        )
    else:
        # Check if email threshold is met
        if any([datetime.now(tz=timezone.utc) < remind_delta_timestamp for remind_delta_timestamp in remind_delta_timestamps]):
            try:
                send_pass_reminder(row['email'], next_pass_time, remind_intervals_names, request_id, 'https://landsatconnect.earth' + url_for('getRequest',request_id=request_id))
            except:
                print('Failed to send email')
        return render_template(
            'request_pending.html',
            next_pass_time=next_pass_time,
            request_id=request_id,
            latitude=row['latitude'],
            longitude=row['longitude']
        )

@app.route('/request/<request_id>/pass/<pass_time>')
def getRequestPass(request_id, pass_time):
    row = get_request(request_id)
    time_range_start, time_range_end = get_time_range_dt(row)
    lsd = LandsatData(
        longitude=row['longitude'],
        latitude=row['latitude'],
        pass_time=pass_time,
        time_range_start=time_range_start,
        time_range_end=time_range_end,
        cloud_cover=row['cloud_cover']
    ) # TODO can we share these between calls?
    metadata = lsd.landsat_metadata()
    return render_template(
        'request_pass_info.html',
        request_id=request_id,
        pass_time=pass_time,
        pass_metadata=metadata
    )

@app.route('/landsat/<request_id>/<pass_time>_rgb.png')
def generateLandsatRGB(request_id, pass_time):
    row = get_request(request_id)
    time_range_start, time_range_end = get_time_range_dt(row)
    pass_datetime = datetime.strptime(pass_time, '%Y-%m-%d_%H:%M:%S')
    lsd = LandsatData(
        longitude=row['longitude'],
        latitude=row['latitude'],
        pass_time=pass_time,
        time_range_start=time_range_start,
        time_range_end=time_range_end,
        cloud_cover=row['cloud_cover']
    )    
    fig = lsd.landsat_rgb()
    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    return Response(output.getvalue(), mimetype='image/png')

@app.route('/landsat/<request_id>/<pass_time>_rgb/download', methods=['GET', 'POST'])
def generateLandsatRGBDownload(request_id, pass_time):
    row = get_request(request_id)
    time_range_start, time_range_end = get_time_range_dt(row)
    pass_datetime = datetime.strptime(pass_time, '%Y-%m-%d_%H:%M:%S')
    lsd = LandsatData(
        longitude=row['longitude'],
        latitude=row['latitude'],
        pass_time=pass_time,
        time_range_start=time_range_start,
        time_range_end=time_range_end,
        cloud_cover=row['cloud_cover']
    )    
    fig = lsd.landsat_rgb()
    file_name = f'landsat_rgb_{request_id}_{pass_time}.png'
    FigureCanvas(fig).print_png('upload/'+file_name)
    return send_file('upload/'+file_name, mimetype='image/png', as_attachment=True, download_name=file_name)

@app.route('/landsat/<request_id>/<pass_time>_tmp.png')
def generateLandsatTmp(request_id, pass_time):
    row = get_request(request_id)
    time_range_start, time_range_end = get_time_range_dt(row)
    lsd = LandsatData(
        longitude=row['longitude'],
        latitude=row['latitude'],
        pass_time=pass_time,
        time_range_start=time_range_start,
        time_range_end=time_range_end,
        cloud_cover=row['cloud_cover']
    )    
    fig = lsd.landsat_temp()
    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    return Response(output.getvalue(), mimetype='image/png')

@app.route('/landsat/<request_id>/<pass_time>_tmp/download')
def generateLandsatTmpDownload(request_id, pass_time):
    row = get_request(request_id)
    time_range_start, time_range_end = get_time_range_dt(row)
    lsd = LandsatData(
        longitude=row['longitude'],
        latitude=row['latitude'],
        pass_time=pass_time,
        time_range_start=time_range_start,
        time_range_end=time_range_end,
        cloud_cover=row['cloud_cover']
    )    
    fig = lsd.landsat_temp()
    file_name = f'landsat_tmp_{request_id}_{pass_time}.png'
    FigureCanvas(fig).print_png('upload/'+file_name)
    return send_file('upload/'+file_name, mimetype='image/png', as_attachment=True, download_name=file_name)

@app.route('/landsat/<request_id>/<pass_time>_ndvi.png')
def generateLandsatNdvi(request_id, pass_time):
    row = get_request(request_id)
    time_range_start, time_range_end = get_time_range_dt(row)
    lsd = LandsatData(
        longitude=row['longitude'],
        latitude=row['latitude'],
        pass_time=pass_time,
        time_range_start=time_range_start,
        time_range_end=time_range_end,
        cloud_cover=row['cloud_cover']
    )    
    fig = lsd.landsat_ndvi()
    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    return Response(output.getvalue(), mimetype='image/png')

@app.route('/landsat/<request_id>/<pass_time>_ndvi/download')
def generateLandsatNdviDownload(request_id, pass_time):
    row = get_request(request_id)
    time_range_start, time_range_end = get_time_range_dt(row)
    lsd = LandsatData(
        longitude=row['longitude'],
        latitude=row['latitude'],
        pass_time=pass_time,
        time_range_start=time_range_start,
        time_range_end=time_range_end,
        cloud_cover=row['cloud_cover']
    )    
    fig = lsd.landsat_ndvi()
    file_name = f'landsat_ndvi_{request_id}_{pass_time}.png'
    FigureCanvas(fig).print_png('upload/'+file_name)
    return send_file('upload/'+file_name, mimetype='image/png', as_attachment=True, download_name=file_name)

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()
    files = glob.glob('upload/*')
    for f in files:
        os.remove(f)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
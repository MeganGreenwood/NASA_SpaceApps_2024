from simplegmail import Gmail

def send_pass_reminder(
    email: str,
    pass_time: str,
    remind_intervals: list[str],
    request_id: int,
    request_url: str
):
  gmail = Gmail() # will open a browser window to ask you to log in and authenticate

  params = {
    "to": f"{email}",
    "sender": "landsat.connect@gmail.com",
    "subject": f"Landsat will be passing over your location in {remind_intervals[0]}",
    "msg_html": f"Your data will be available here: {request_url}",
  }
  message = gmail.send_message(**params)
  return

from dotenv import load_dotenv
from datetime import datetime
import json
import requests
import os

load_dotenv()
# TODO Handle token in production

def landsat_8_passes(
        latitude: float,
        longitude: float,
        limit: int = 1
):
    norad_id = 39084 # LANDSAT 8
    observer_lat = latitude
    observer_lng = longitude
    observer_alt = 1000 # TODO make this dynamic?
    days = 10
    min_elevation = 76 # LANDSAT swath width is approx. 14 degrees

    res = requests.get(f'https://api.n2yo.com/rest/v1/satellite/radiopasses/{norad_id}/{observer_lat}/{observer_lng}/{observer_alt}/{days}/{min_elevation}&apiKey={os.environ["N2YO_API_TOKEN"]}')
    res_j = json.loads(res.text)
    passes = []
    for item in res_j['passes']:
        passes.append(datetime.fromtimestamp(item['startUTC']).strftime('%c'))
    return passes[:limit]

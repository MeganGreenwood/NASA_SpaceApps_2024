from dotenv import load_dotenv
from datetime import datetime, timezone
import json
import requests
import os

load_dotenv()
# TODO Handle token in production

def landsat_passes_given_sat_id(
        latitude: float,
        longitude: float,
        norad_id: int
):
    observer_lat = latitude
    observer_lng = longitude
    observer_alt = 1000 # TODO make this dynamic?
    days = 10
    min_elevation = 83 # LANDSAT swath width is approx. 14 degrees

    # print(f'https://api.n2yo.com/rest/v1/satellite/radiopasses/{norad_id}/{observer_lat}/{observer_lng}/{observer_alt}/{days}/{min_elevation}&apiKey={os.environ["N2YO_API_TOKEN"]}')
    res_ls = requests.get(f'https://api.n2yo.com/rest/v1/satellite/radiopasses/{norad_id}/{observer_lat}/{observer_lng}/{observer_alt}/{days}/{min_elevation}&apiKey={os.environ["N2YO_API_TOKEN"]}')
    res_j = json.loads(res_ls.text)
    # print(res_j)
    # print(time_range_start)
    passes = []
    if 'passes' in res_j.keys():
        for item in res_j['passes']:
            pass_time = datetime.fromtimestamp(item['startUTC'], tz=timezone.utc)
            # if time_range_end is not None and time_range_start is not None:
            #     if pass_time > time_range_start and pass_time < time_range_end:
            passes.append(pass_time)
            # else:
                # passes.append(pass_time)
    return passes

def landsat_passes(
        latitude,
        longitude
) -> list[str]:
    ls_8_passes = landsat_passes_given_sat_id(
        latitude=latitude,
        longitude=longitude,
        norad_id=39084 # LANDSAT 8
    )
    ls_9_passes = landsat_passes_given_sat_id(
        latitude=latitude,
        longitude=longitude,
        norad_id=49260 # LANDSAT 9
    )

    all_passes = ls_8_passes + ls_9_passes
    all_passes_sorted = sorted(all_passes)


    return all_passes_sorted

# print(landsat_passes(-33.96245606251111, 149.9673963028338, limit=3))

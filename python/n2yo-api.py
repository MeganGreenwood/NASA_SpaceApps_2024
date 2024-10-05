from dotenv import load_dotenv
import requests
import os

load_dotenv()

res = requests.get(f'https://api.n2yo.com/rest/v1/satellite/tle/39084&apiKey={os.environ["N2YO_API_TOKEN"]}')
print(res.text)
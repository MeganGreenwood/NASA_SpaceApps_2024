import pystac_client
import planetary_computer
# import odc.stac
# import matplotlib.pyplot as plt

from pystac.extensions.eo import EOExtension as eo

catalog = pystac_client.Client.open(
    "https://planetarycomputer.microsoft.com/api/stac/v1"
    # modifier=planetary_computer.sign_inplace,
)

bbox_of_interest = [-122.2751, 47.5469, -121.9613, 47.7458]
time_of_interest = "2021-01-01/2021-12-31"

search = catalog.search(
    collections=["landsat-c2-l2"],
    bbox=bbox_of_interest,
    datetime=time_of_interest,
    query={"eo:cloud_cover": {"lt": 10}},
)

items = search.item_collection()
print(f"Returned {len(items)} Items")
for item in items:
    print(item.__str__())

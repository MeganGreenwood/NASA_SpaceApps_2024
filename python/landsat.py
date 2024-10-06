import pystac_client
import planetary_computer
import odc.stac
import matplotlib.pyplot as plt

from pystac.extensions.eo import EOExtension as eo

def landsat_catalog_search(
        latitude: float,
        longitude: float
):
    bbox_xmin = longitude - 0.0006
    bbox_ymin = latitude - 0.0006
    bbox_xmax = longitude + 0.0006
    bbox_ymax = latitude + 0.0006

    input_start = "2024-05-01" # TODO pass this in dynamically
    input_end = "2024-12-31"

    bbox_of_interest = [bbox_xmin, bbox_ymin, bbox_xmax, bbox_ymax]
    time_of_interest = f"{input_start}/{input_end}"

    catalog = pystac_client.Client.open(
        "https://planetarycomputer.microsoft.com/api/stac/v1",
        modifier=planetary_computer.sign_inplace,
    )

    #Obtain user input maximum cloud cover from Tracking Request page
    input_cloud_cover = 0.1
    input_cloud_cover = input_cloud_cover * 100

    #Search current landsat level 2 data catalog for all images containing the specified bounding box, in the specified time period
    #Returns only images from Landsat-8/landsat-9 below the maximum cloud cover threshold 
    search = catalog.search(
        collections=["landsat-c2-l2"],
        bbox=bbox_of_interest,
        datetime=time_of_interest,
        query={
            "eo:cloud_cover": {"lt": input_cloud_cover},
            "platform": {"in": ["landsat-8", "landsat-9"]},
        },
    )

    items = search.item_collection()

    selected_item = max(items, key=lambda item: item.datetime)

    bands_of_interest = ["nir08", "red", "green", "blue", "qa_pixel", "lwir11"]
    data = odc.stac.stac_load(
        [selected_item], bands=bands_of_interest, bbox=bbox_of_interest
    ).isel(time=0)

    fig, ax = plt.subplots(figsize=(10, 10))

    coords = data[["red", "green", "blue"]].to_dataarray()
    coords.plot.imshow(robust=True, ax=ax)
    ax.set_title("Natural Color Image")
    return fig

# landsat_catalog_search(-33.96245606251111, 149.9673963028338)

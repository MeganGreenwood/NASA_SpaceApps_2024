from datetime import datetime, timedelta
import pystac_client
import planetary_computer
import odc.stac
import matplotlib.pyplot as plt

# from pystac.extensions.eo import EOExtension as eo

class LandsatData:
    def __init__(
            self,
            latitude: float,
            longitude: float,
            time_range_start: datetime | None = None,
            time_range_end: datetime | None = None,
            pass_time: datetime | None = None,
            cloud_cover: float = 0.3
    ):
        self.latitude = latitude
        self.longitude = longitude
        self.bbox_xmin = longitude - 0.0008
        self.bbox_ymin = latitude - 0.0008
        self.bbox_xmax = longitude + 0.0008
        self.bbox_ymax = latitude + 0.0008

        if time_range_start is not None and time_range_end is not None:
            self.input_start = time_range_start.strftime('%Y-%m-%d')
            self.input_end = time_range_end.strftime('%Y-%m-%d')
        elif pass_time is not None:
            self.input_start = pass_time.strftime('%Y-%m-%d')
            self.input_end = None
        else:
            print('No time data selected for satellite pass')
            self.items = []
            return

        self.bbox_of_interest = [self.bbox_xmin, self.bbox_ymin, self.bbox_xmax, self.bbox_ymax]
        if self.input_end is not None:
            self.time_of_interest = f"{self.input_start}/{self.input_end}"
        else:
            self.time_of_interest = self.input_start
        # print(self.time_of_interest)

        # Note: A limitation of this data source is that it only has older data
        self.catalog = pystac_client.Client.open(
            "https://planetarycomputer.microsoft.com/api/stac/v1",
            modifier=planetary_computer.sign_inplace,
        )

        #Obtain user input maximum cloud cover from Tracking Request page
        input_cloud_cover = cloud_cover * 100

        #Search current landsat level 2 data catalog for all images containing the specified bounding box, in the specified time period
        #Returns only images from Landsat-8/landsat-9 below the maximum cloud cover threshold 
        search = self.catalog.search(
            collections=["landsat-c2-l2"],
            bbox=self.bbox_of_interest,
            datetime=self.time_of_interest,
            query={
                "eo:cloud_cover": {"lt": input_cloud_cover},
                "platform": {"in": ["landsat-8", "landsat-9"]},
            },
        )

        self.items = search.item_collection()
        # print(len(self.items))

        if len(self.items) == 0:
            self.selected_item = None
            self.data = None
            return

        self.selected_item = max(self.items, key=lambda item: item.datetime)

        bands_of_interest = ["nir08", "red", "green", "blue", "qa_pixel", "lwir11"]
        self.data = odc.stac.stac_load(
            [self.selected_item], bands=bands_of_interest, bbox=self.bbox_of_interest
        ).isel(time=0)


    def landsat_rgb(
            self
    ):

        fig, ax = plt.subplots(figsize=(10, 10))

        coords = self.data[["red", "green", "blue"]].to_dataarray()
        coords.plot.imshow(robust=True, ax=ax)
        ax.set_title("Natural Color Image")
        return fig

    # landsat_catalog_search(-33.96245606251111, 149.9673963028338)


    def landsat_temp(
            self
    ):

        band_info = self.selected_item.assets["lwir11"].extra_fields["raster:bands"][0]

        temperature = self.data["lwir11"].astype(float)
        temperature *= band_info["scale"]
        temperature += band_info["offset"]
        temperature[:5, :5]

        #Convert temperature from Kelvin to Celsius 
        celsius = temperature - 273.15

        #Plot surface temperature
        fig, ax = plt.subplots(figsize=(13, 10))
        celsius.plot.imshow(ax=ax, cmap="magma")
        ax.set_title("Surface Temperature")

        return fig

    def landsat_ndvi(self):

        #Define bands needed to calculate NDVI
        red = self.data["red"].astype("float")
        nir = self.data["nir08"].astype("float")

        #Calculate NDVI
        ndvi = (nir - red) / (nir + red)

        #Plot NDVI
        fig, ax = plt.subplots(figsize=(13, 10))
        ndvi.plot.imshow(ax=ax, cmap="viridis")
        ax.set_title("Normalized Difference Vegetation Index (NDVI)")
        return fig

    def landsat_metadata(
            self
    ):
        if self.selected_item is None:
            return "No data found"

        return f"""
        Image Metadata <br/>
        Capture Time: {self.selected_item.properties["datetime"]}<br>
        Satellite: {self.selected_item.properties["platform"]}<br>
        Scene ID: {self.selected_item.properties["landsat:scene_id"]}<br>
        WRS2: Path {self.selected_item.properties["landsat:wrs_path"]}, Row {self.selected_item.properties["landsat:wrs_row"]}<br>
        Cloud Cover: {self.selected_item.properties["eo:cloud_cover"]}%
    """

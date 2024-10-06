class formSubmission:
    def __init__(
            self,
            latitude,
            longitude,
            track_period,
            time_range,
            cloud_cover,
            notification_frequency_15m,
            email
    ):
        self.latitude = latitude
        self.longitude = longitude
        self.track_period = track_period
        self.time_range = time_range
        self.cloud_cover = cloud_cover
        self.notification_frequency_15m = notification_frequency_15m
        self.email = email

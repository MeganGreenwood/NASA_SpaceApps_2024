class formSubmission:
    def __init__(
            self,
            latitude,
            longitude,
            track_period,
            time_range_start,
            time_range_end,
            cloud_cover,
            notification_frequency_15m,
            notification_frequency_30m,
            notification_frequency_1hr,
            notification_frequency_6hr,
            notification_frequency_12hr,
            notification_frequency_1d,
            notification_frequency_1w,
            email
    ):
        self.latitude = latitude
        self.longitude = longitude
        self.track_period = track_period
        self.time_range_start = time_range_start
        self.time_range_end = time_range_end
        self.cloud_cover = cloud_cover
        self.notification_frequency_15m = notification_frequency_15m
        self.notification_frequency_30m = notification_frequency_30m
        self.notification_frequency_1hr = notification_frequency_1hr
        self.notification_frequency_6hr = notification_frequency_6hr
        self.notification_frequency_12hr = notification_frequency_12hr
        self.notification_frequency_1d = notification_frequency_1d
        self.notification_frequency_1w = notification_frequency_1w
        self.email = email

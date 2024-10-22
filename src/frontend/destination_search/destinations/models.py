from django.db import models


class CoreAirports(models.Model):
    iata_code = models.CharField(primary_key=True, max_length=3)
    airport_name = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=255, blank=True, null=True)
    lat = models.DecimalField(max_digits=10, decimal_places=7)
    lon = models.DecimalField(max_digits=10, decimal_places=7)
    passenger_count = models.CharField(max_length=15, blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'core_airports'


class CoreCategories(models.Model):
    category_id = models.IntegerField(primary_key=True)
    category_name = models.CharField(max_length=255)
    description = models.CharField(max_length=500, blank=True, null=True)
    display_order = models.IntegerField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    axis_title = models.CharField(max_length=50, blank=True, null=True)
    axis_label_low = models.CharField(max_length=50, blank=True, null=True)
    axis_label_high = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'core_categories'

    def __str__(self):
        return str(self.category_id)


class CoreDimensions(models.Model):
    category_id = models.ForeignKey(CoreCategories, models.DO_NOTHING, db_column='category_id')
    dimension_id = models.IntegerField(primary_key=True)
    dimension_name = models.CharField(max_length=255, blank=True, null=True)
    description = models.CharField(max_length=500, blank=True, null=True)
    extras = models.CharField(max_length=255, blank=True, null=True)
    icon_url = models.CharField(max_length=255, blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    raw_value_decimals = models.CharField(max_length=255, blank=True, null=True)
    raw_value_unit = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'core_dimensions'

    def __str__(self):
        return str(self.dimension_id)


class CoreLocations(models.Model):
    location_id = models.BigIntegerField(primary_key=True)
    city = models.TextField(blank=True, null=True)
    county = models.TextField(blank=True, null=True)
    state = models.TextField(blank=True, null=True)
    country = models.TextField(blank=True, null=True)
    country_code = models.TextField(blank=True, null=True)
    address_type = models.TextField(blank=True, null=True)
    population = models.BigIntegerField(blank=True, null=True)
    lat = models.TextField(blank=True, null=True)
    lon = models.TextField(blank=True, null=True)
    radius_km = models.BigIntegerField(blank=True, null=True)
    box_bottom_left_lat = models.TextField(blank=True, null=True)
    box_bottom_left_lon = models.TextField(blank=True, null=True)
    box_top_right_lat = models.TextField(blank=True, null=True)
    box_top_right_lon = models.TextField(blank=True, null=True)
    geojson = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    airport_1 = models.CharField(max_length=3, blank=True, null=True)
    airport_2 = models.CharField(max_length=3, blank=True, null=True)
    airport_3 = models.CharField(max_length=3, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'core_locations'

    def __str__(self):
        return self.city
    

class CoreLocationsImages(models.Model):
    location_id = models.OneToOneField(CoreLocations, models.DO_NOTHING, primary_key=True, db_column='location_id')
    img_url = models.CharField(max_length=1024, blank=True, null=True)
    source = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'core_locations_images'

class CoreRefStartLocations(models.Model):
    location_id = models.BigIntegerField(primary_key=True)
    city = models.TextField(blank=True, null=True)
    country = models.TextField(blank=True, null=True)
    country_code = models.TextField(blank=True, null=True)
    lat = models.TextField(blank=True, null=True)
    lon = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    mapped_start_airport = models.CharField(max_length=5, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'core_ref_start_locations'


class CoreScores(models.Model):
    location_id = models.OneToOneField(CoreLocations, models.DO_NOTHING, primary_key=True, db_column='location_id')
    category_id = models.ForeignKey(CoreCategories, models.DO_NOTHING, db_column='category_id')
    dimension_id = models.ForeignKey(CoreDimensions, models.DO_NOTHING, db_column='dimension_id')
    start_date = models.DateField()
    end_date = models.DateField()
    ref_start_location_id = models.ForeignKey(CoreRefStartLocations, models.DO_NOTHING, db_column='ref_start_location_id')
    score = models.DecimalField(max_digits=10, decimal_places=5, blank=True, null=True)
    raw_value = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'core_scores'
        unique_together = (('location_id', 'category_id', 'dimension_id', 'start_date', 'end_date'),)


class CoreTexts(models.Model):
    location_id = models.OneToOneField(CoreLocations, models.DO_NOTHING, primary_key=True, db_column='location_id')
    category_id = models.ForeignKey(CoreCategories, models.DO_NOTHING, db_column='category_id')
    start_date = models.DateField()
    end_date = models.DateField()
    ref_start_location_id = models.ForeignKey(CoreRefStartLocations, models.DO_NOTHING, db_column='ref_start_location_id')
    text_general = models.TextField()
    text_anomaly = models.TextField()
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'core_texts'
        unique_together = (('location_id', 'category_id'),)


class RawWeatherHistorical(models.Model):
    location_id = models.OneToOneField(CoreLocations, models.DO_NOTHING, primary_key=True, db_column='location_id')
    city = models.CharField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=255, blank=True, null=True)
    year = models.IntegerField()
    month = models.IntegerField()
    temperature_max = models.DecimalField(max_digits=10, decimal_places=5, blank=True, null=True)
    temperature_min = models.DecimalField(max_digits=10, decimal_places=5, blank=True, null=True)
    sunshine_duration = models.DecimalField(max_digits=10, decimal_places=5, blank=True, null=True)
    daylight_duration = models.DecimalField(max_digits=10, decimal_places=5, blank=True, null=True)
    precipitation_duration = models.DecimalField(max_digits=10, decimal_places=5, blank=True, null=True)
    precipitation_sum = models.DecimalField(max_digits=10, decimal_places=5, blank=True, null=True)
    rain_sum = models.DecimalField(max_digits=10, decimal_places=5, blank=True, null=True)
    snowfall_sum = models.DecimalField(max_digits=10, decimal_places=5, blank=True, null=True)
    wind_speed_max = models.DecimalField(max_digits=11, decimal_places=7, blank=True, null=True)
    weather_code_label = models.CharField(max_length=255, blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'raw_weather_historical'
        unique_together = (('location_id', 'year', 'month'),)

class RawTravelWarnings(models.Model):
    country_code = models.CharField(primary_key=True, max_length=2)
    country_name = models.CharField(max_length=64, blank=True, null=True)
    warning_text = models.TextField(blank=True, null=True)
    link = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'raw_travel_warnings'

class RawCultureSights(models.Model):
    location_id = models.OneToOneField(CoreLocations, models.DO_NOTHING, primary_key=True, db_column='location_id')
    sight_rank = models.IntegerField()
    sight = models.CharField(max_length=100, blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'raw_culture_sights'
        unique_together = (('location_id', 'sight_rank'),)


class RawCurrencyTexts(models.Model):
    location_id = models.OneToOneField(CoreLocations, models.DO_NOTHING, primary_key=True, db_column='location_id')
    country_code = models.TextField(blank=True, null=True)
    category_id = models.BigIntegerField(blank=True, null=True)
    text = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'raw_currency_texts'


class RawReachabilityLand(models.Model):
    location_id = models.OneToOneField(CoreLocations, models.DO_NOTHING, primary_key=True, db_column='loc_id')
    ref_start_location_id = models.ForeignKey(CoreRefStartLocations, models.DO_NOTHING, db_column='ref_id')
    arr_city = models.CharField(max_length=255, blank=True, null=True)
    dep_city = models.CharField(max_length=255, blank=True, null=True)
    car_distance = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    car_duration = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    car_polyline = models.TextField(blank=True, null=True)
    car_geojson = models.TextField(blank=True, null=True)
    pt_distance = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    pt_duration = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    pt_polyline = models.TextField(blank=True, null=True)
    pt_geojson = models.TextField(blank=True, null=True)
    pt_total_transfers = models.IntegerField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'raw_reachability_land'
        unique_together = (('location_id', 'ref_start_location_id'),)
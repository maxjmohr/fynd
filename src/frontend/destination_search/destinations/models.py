from django.db import models


class CoreCategories(models.Model):
    category_id = models.IntegerField(primary_key=True)
    category_name = models.CharField(max_length=255)
    description = models.CharField(max_length=500, blank=True, null=True)
    display_order = models.IntegerField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'core_categories'


class CoreDimensions(models.Model):
    category_id = models.ForeignKey(CoreCategories, models.DO_NOTHING, db_column='category_id')
    dimension_id = models.IntegerField(primary_key=True)
    dimension_name = models.CharField(max_length=255, blank=True, null=True)
    description = models.CharField(max_length=500, blank=True, null=True)
    extras = models.CharField(max_length=255, blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'core_dimensions'


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


class CoreScores(models.Model):
    location_id = models.OneToOneField(CoreLocations, models.DO_NOTHING, primary_key=True, db_column='location_id')
    category_id = models.ForeignKey(CoreCategories, models.DO_NOTHING, db_column='category_id')
    dimension_id = models.ForeignKey(CoreDimensions, models.DO_NOTHING, db_column='dimension_id')
    score = models.DecimalField(max_digits=10, decimal_places=5, blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        managed = False
        db_table = 'core_scores'
        unique_together = (('location_id', 'category_id', 'dimension_id', 'start_date', 'end_date'),)
from django.contrib.gis.db import models
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

import timedelta
import json

from tracks.polyline import encode_coords

class Activity(models.Model):

    STRAVA_PROVIDER = 'strava'

    DATA_PROVIDERS = (
        (STRAVA_PROVIDER, u'Strava provider'),
    )

    user = models.ForeignKey('auth.User')
    guID = models.CharField(max_length=255, unique=True)
    start_date = models.DateTimeField(blank=True, null=True)
    provider = models.CharField(max_length=100, db_index=True, choices=DATA_PROVIDERS)
    start_point = models.PointField(blank=True, null=True)
    polyline = models.TextField(blank=True, null=True)
    resource_state = models.PositiveIntegerField(blank=True, null=True)
    moving_time = timedelta.fields.TimedeltaField(blank=True, null=True)
    distance = models.DecimalField(blank=True, null=True, max_digits=16, decimal_places=6)
    description = models.TextField(blank=True, null=True)
    total_elevation_gain = models.DecimalField(blank=True, null=True, max_digits=10, decimal_places=2)
    location_city = models.CharField(blank=True, null=True, max_length=255)
    location_country = models.CharField(blank=True, null=True, max_length=255)
    average_speed = models.DecimalField(blank=True, null=True, max_digits=10, decimal_places=2)
    calories = models.DecimalField(blank=True, null=True, max_digits=10, decimal_places=2)
    route = models.LineStringField(blank=True, null=True)


    # shard_id + note_id for evernote
    shard_id = models.CharField(max_length=255, blank=True, null=True)
    note_id = models.CharField(max_length=255, blank=True, null=True)

    def __unicode__(self):
        return self.guID

    def get_mapbox_static_image(self):
        '''
        https://www.mapbox.com/developers/api/static/
        :return: url on mapbox static maps image
        '''
        if not all([
            settings.MAPBOX_API_ENDPOINT,
            settings.MAPBOX_API_TOKEN,
            settings.MAPBOX_MAP_ID
        ]):
            raise ImproperlyConfigured('Check your MAPBOX configuration settings')
        if not self.route:
            return None

        # simplify geometry
        coords = self.route.simplify(0.0001).coords

        # styling gejson



        # get centroid to fit all geometry into bbox
        lon, lat = self.route.centroid.coords

        url = u"%(endpoint)s/%(mapid)s/path-4+026-0.75(%(polyline)s)/%(lon)s,%(lat)s,13/500x500.png?access_token=%(access_token)s" % {
            'endpoint': settings.MAPBOX_API_ENDPOINT,
            'mapid': settings.MAPBOX_MAP_ID,
            'lon': lon,
            'lat': lat,
            'access_token': settings.MAPBOX_API_TOKEN,
            'polyline': encode_coords(coords)

        }
        return url



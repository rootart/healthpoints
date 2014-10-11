from django.contrib.gis.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.contrib.gis.measure import D
from django.db.models import Count, Min, Sum, Avg

import timedelta
import json

import facebook
from social.apps.django_app.default.models import UserSocialAuth

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

    # fb id
    fb_id = models.CharField(max_length=255, db_index=True, blank=True, null=True)

    def __unicode__(self):
        return self.guID

    @property
    def location(self):
        return u"{}, {}".format(self.location_city, self.location_country)

    @property
    def metrics_msg(self):
        return u"{}m, in {}, with {}m of elevation gain".format(
            self.distance, self.moving_time, self.total_elevation_gain
        )

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
        coords = self.route.simplify(0.0001).coords[0:60]

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

    def fb_post_activity(self):
        '''
        Post FB activity
        :return: FB object GUID 865772796780594_866207356737138
        '''
        token = self.user.social_auth.get(provider='facebook').tokens

        api = facebook.GraphAPI(token)


        resp = api.put_wall_post(
            self.metrics_msg,
            attachment={
                'caption': self.location,
                'picture': self.get_mapbox_static_image()
            }
        )

        self.fb_id = resp['id']
        self.save()
        return self.fb_id

    @property
    def likes(self):
        return self.activityfbactions_set.filter(activity_type=ActivityFBActions.LIKE)

    @property
    def comments(self):
        return self.activityfbactions_set.filter(activity_type=ActivityFBActions.COMMENT)

    @property
    def formated_distance(self):
        '''
        :return: Formated distance in KM
        '''
        return D(m=self.distance).km


    @classmethod
    def user_stats(cls, user):
        activities = cls.objects.filter(user=user)
        total_distance = D(m=activities.aggregate(total_distance = Sum('distance'))['total_distance'] or 0).km
        total_elevation_gain_distance = D(
            m=activities.aggregate(total_elevation_gain=Sum('total_elevation_gain'))['total_elevation_gain'] or 0
        ).km

        total_calories = activities.aggregate(total_calories=Sum('calories'))['total_calories']
        total_moving_time = activities.aggregate(total_moving_time=Sum('moving_time'))['total_moving_time']
        total_likes = ActivityFBActions.objects.filter(
            activity__user=user,
            activity_type=ActivityFBActions.LIKE
            ).count()

        return {
            'total_distance': total_distance,
            'total_activities': activities.count(),
            'elevation_gain': total_elevation_gain_distance,
            'total_moving_time': total_moving_time,
            'total_calories': total_calories,
            'total_likes': total_likes
        }



class ActivityFBActions(models.Model):
    LIKE = 'like'
    COMMENT = 'comment'
    ACTIVITY_CHOICES = (
        (LIKE, "Like"),
        (COMMENT, "Comment")
    )
    activity = models.ForeignKey('tracks.Activity')
    activity_type = models.CharField(choices=ACTIVITY_CHOICES,
                                     max_length=100,
                                     db_index=True
    )
    fb_id = models.CharField(
        max_length=255,blank=True,
        null=True, db_index=True
    )
    username = models.CharField(blank=True, null=True, max_length=255)
    user_fb_id = models.CharField(max_length=255, blank=True, null=True)
    user_picture_url = models.CharField(max_length=500, blank=True, null=True)
    comment = models.TextField(blank=True, null=True)


@receiver(post_save, sender=UserSocialAuth)
def create_profile_for_user(sender, instance, created, **kwargs):
    """
    Fetch strava data after receiving strava token
    """
    from tracks.tasks import load_strava_data
    if instance.provider == 'strava':
        load_strava_data.delay(instance.user.id)

import hashlib
import binascii
import timedelta
import json
import cStringIO

from django.contrib.gis.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.contrib.gis.measure import D
from django.db.models import Count, Min, Sum, Avg

import facebook
from social.apps.django_app.default.models import UserSocialAuth
from evernote.api.client import EvernoteClient
import evernote.edam.type.ttypes as Types
import evernote.edam.userstore.constants as UserStoreConstants
from evernote.edam.error.ttypes import EDAMUserException
from evernote.edam.error.ttypes import EDAMSystemException
from evernote.edam.error.ttypes import EDAMNotFoundException

import requests
from PIL import Image


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
    note_url = models.CharField(max_length=255, blank=True, null=True)

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

    def evenote_publish_note(self):
        '''
        Publish note into evernote cloud to `HealthPoints` notebooks
        :return:
        '''
        assert self.user.social_auth.filter(provider='evernote-sandbox').count() == 1

        NOTEBOOK_NAME = getattr(settings, 'NOTEBOOK_NAME', 'HealthPoints')

        try:
            token = self.user.social_auth.get(provider='evernote-sandbox').tokens['oauth_token']
            client = EvernoteClient(token=token)
        except EDAMUserException as e:

            print "Error attempting to authenticate to Evernote: %s" % e.parameter
            return False
        except EDAMSystemException as e:
            print "Error attempting to authenticate to Evernote: %s" % e.message
            return False


        # get user store object
        userStore = client.get_user_store()
        user = userStore.getUser()

        # fetch list of existing notes
        noteStore = client.get_note_store()
        notebooks = noteStore.listNotebooks()

        # create new object if doesn't exists
        notebooks = {n.name:n for n in notebooks}
        if NOTEBOOK_NAME not in notebooks:
            notebook = Types.Notebook()
            notebook.name = NOTEBOOK_NAME
            notebook = noteStore.createNotebook(notebook)
        else:
            notebook = notebooks[NOTEBOOK_NAME]

        notebookGuid = notebook.guid

        activityNote = Types.Note()
        activityNote.title = u"{} - {}".format(self.location, self.start_date)

        info = "Place: %s " \
               "Date: %s " \
               "Distance: %s" % (
            self.location, self.start_date, self.formated_distance
        )


        activityNote.notebookGuid = notebookGuid

        _file = cStringIO.StringIO(requests.get(self.get_mapbox_static_image()).content)
        image = _file.read()
        md5 = hashlib.md5()
        md5.update(image)
        hash = md5.digest()

        data = Types.Data()
        data.size = len(image)
        data.bodyHash = hash
        data.body = image

        resource = Types.Resource()
        resource.mime = 'image/png'
        resource.data = data

        hash_hex = binascii.hexlify(hash)


        body = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
        body += "<!DOCTYPE en-note SYSTEM \"http://xml.evernote.com/pub/enml2.dtd\">"
        body += "<en-note>%s" % info
        body += '<en-media type="image/png" hash="' + hash_hex + '"/>'
        body += "</en-note>"
        activityNote.content = body

        activityNote.resources = [resource]

        activityNote = noteStore.createNote(activityNote)

        noteKey = noteStore.shareNote(activityNote.guid)


        url = "https://sandbox.evernote.com/shard/%(shardID)s/sh/%(noteGuid)s/%(noteKey)s" % {
            'shardID': user.shardId,
            'noteGuid': activityNote.guid,
            'noteKey': noteKey
        }

        self.shard_id = user.shardId,
        self.note_id = noteKey,
        self.note_url = url
        self.save()
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

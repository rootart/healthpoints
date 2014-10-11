from django.contrib.auth.models import User
from django.contrib.gis.geos import Point, LineString

from celery import task
from celery.schedules import crontab

from stravalib import Client as StravaClient
from stravalib import unithelper
import facebook

from polyline import decode as polyline_decode

from tracks.models import Activity, ActivityFBActions


@task
def load_strava_data(user_id):
    user = User.objects.get(id=user_id)
    token = user.social_auth.get(provider='strava').tokens

    c = StravaClient(token)
    # fetch 200 activities
    activities = c.get_activities(limit=200)

    for track in activities:
        activity, created = Activity.objects.get_or_create(
            guID=track.id,
            user=user
        )
        print track.id
        activity.provider = Activity.STRAVA_PROVIDER
        activity.location_city = track.location_city
        activity.location_country = track.location_country

        full_activity = c.get_activity(track.id)
        activity.polyline = full_activity.map.polyline
        activity.moving_time = full_activity.moving_time
        activity.start_date = full_activity.start_date

        activity.distance = float(
            unithelper.meters(
                track.distance
            )
        )

        activity.total_elevation_gain = float(
            unithelper.meters(
                track.total_elevation_gain
            )
        )
        activity.resource_state = track.resource_state
        activity.description = track.description
        if hasattr(track, 'start_latlng') and track.start_latlng is not None:
            activity.start_point = Point(
                track.start_latlng.lon,
                track.start_latlng.lat
            )

        activity.save()

        if activity.polyline:
            activity.route = LineString(polyline_decode(activity.polyline))
        activity.save()



@task.periodic_task(
    run_every=crontab(minute="*/15")
)
def update_fb_actions():

    activities = Activity.objects.filter(
        fb_id__isnull=False
    )
    for activity in activities:
        graph = facebook.GraphAPI(
            activity.user.social_auth.get(provider='facebook').tokens
        )

        # fetch likes
        likes = graph.get_object('/%s/likes' % activity.fb_id)['data']
        for like in likes:
            action, created = ActivityFBActions.objects.get_or_create(
                activity=activity,
                user_fb_id=like['id'],
                activity_type=ActivityFBActions.LIKE
            )
            if created:
                action.username = like['name']
                action.user_picture_url = graph.get_object('%s/picture' % like['id'])['url']
                action.save()


        # fetch comments
        # TODO DRY code
        comments = graph.get_object('/%s/comments' % activity.fb_id)['data']
        for comment in comments:
            action, created = ActivityFBActions.objects.get_or_create(
                activity=activity,
                fb_id=like['id'], # id of comment
                activity_type=ActivityFBActions.COMMENT
            )
            if created:
                action.username = comment['from']['name']
                action.user_fb_id = comment['from']['id']
                action.comment = comment['message']
                action.user_picture_url = graph.get_object('%s/picture' % comment['from']['id'])['url']
                action.save()



from django.contrib.auth.models import User
from django.contrib.gis.geos import Point, LineString

from celery import task

from stravalib import Client as StravaClient
from stravalib import unithelper

from polyline import decode as polyline_decode

from tracks.models import Activity


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



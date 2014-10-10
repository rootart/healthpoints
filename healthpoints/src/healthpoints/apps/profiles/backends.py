import json
from urllib import urlencode

from social.backends.oauth import BaseOAuth2


class StravaOAuth2(BaseOAuth2):
    """Strava OAuth1 authentication backend"""
    name = 'strava'
    AUTHORIZATION_URL = 'https://www.strava.com/oauth/authorize'
    ACCESS_TOKEN_URL = 'https://www.strava.com/oauth/token'
    SCOPE_SEPARATOR = ' '
    DEFAULT_SCOPE = ['write']
    STATE_PARAMETER = 'racelist-state'
    ACCESS_TOKEN_METHOD = 'POST'
    REDIRECT_STATE = False
    EXTRA_DATA = [
        ('id', 'id'),
        ('firstname', 'first_name'),
        ('lastname', 'last_name'),
        ('email', 'email')]

    def get_user_id(self, details, response):
        return response['id']

    def get_user_details(self, response):
        """Return user details from Strava account"""
        data= {'username': u'{}'.format(response.get('id')),
                'email': response.get('email'),
                'first_name': response.get('firstname'),
                'last_name': response.get('lastname')
            }
        print data
        return data

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        url = 'https://www.strava.com/api/v3/athlete?' + urlencode({
            'access_token': access_token
        })
        print self.get_json(url)
        try:
            return self.get_json(url)
        except ValueError:
            return None

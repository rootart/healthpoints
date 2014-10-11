from django import template
from django.core.cache import cache

register = template.Library()


import facebook


@register.inclusion_tag('tracks/includes/profile-block.html')
def render_profile_block(user):
    social_auth = user.social_auth.get(provider='facebook')
    api = facebook.GraphAPI(
        social_auth.tokens
    )
    picture = cache.get('user-picture-%s' % user.id)
    if not picture:
        picture = api.get_object('%s/picture?width=120&heigh=120' % social_auth.uid)['url']
        cache.set('user-picture-%s' % user.id, picture)

    return {
        'picture': picture,
        'user': user
    }






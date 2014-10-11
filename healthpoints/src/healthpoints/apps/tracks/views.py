from django.shortcuts import render
from django.views.generic import TemplateView

from braces import views

from tracks.models import Activity


class MainView(TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs):
        context = super(MainView, self).get_context_data()
        user = self.request.user
        if self.request.user.is_authenticated():
            activities = Activity.objects.filter(
                user=user
            ).select_related('activityfbactions')
        context['activities'] = activities

        context['stats'] = Activity.user_stats(self.request.user)
        return context



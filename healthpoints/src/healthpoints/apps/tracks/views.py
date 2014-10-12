from django.shortcuts import render
from django.views.generic import TemplateView, View, RedirectView
from django.http import HttpResponseRedirect
from django.contrib.auth import logout
from django.core.urlresolvers import reverse

from braces import views

from tracks.models import Activity, ActivityFBActions


class DemoProfileView(TemplateView):
    template_name = 'demo-profile.html'


class MainView(TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs):
        context = super(MainView, self).get_context_data()
        user = self.request.user
        activities = []
        if self.request.user.is_authenticated():
            activities = Activity.objects.filter(
                user=user
            ).select_related('activityfbactions')
            context['stats'] = Activity.user_stats(self.request.user)

            support_team = ActivityFBActions.objects.filter(activity__user=user).distinct('user_fb_id')
            context['support_team'] = support_team

            context['health_points'] = Activity.get_health_points(user)
        context['activities'] = activities


        return context


class LogoutView(RedirectView):
    def get(self, request, *args, **kwargs):
        logout(request)
        return HttpResponseRedirect(reverse('main'))


class ShareFBView(
    views.CsrfExemptMixin, views.AjaxResponseMixin, views.LoginRequiredMixin,
    views.JSONRequestResponseMixin, View):
    '''
    Share activity to facebook
    '''
    def post_ajax(self, request, *args, **kwargs):
        activity_id = int(request.POST.get('id'))
        try:
            activity = Activity.objects.get(
                id=activity_id,
                user =  request.user
            )
        except Activity.DoesNotExist:
            data = {
                'status': False,
                'msg': 'Activity is either missing or you do not have permissions'
            }
        else:
            data = {
                'status': True,
                'link': activity.fb_post_activity()
            }
        return self.render_json_response(data)


class ShareEvernoteView(
    views.CsrfExemptMixin, views.AjaxResponseMixin, views.LoginRequiredMixin,
    views.JSONRequestResponseMixin, View):
    '''
    Share activity to facebook
    '''
    def post_ajax(self, request, *args, **kwargs):
        activity_id = int(request.POST.get('id'))
        try:
            activity = Activity.objects.get(
                id=activity_id,
                user = request.user
            )
        except Activity.DoesNotExist:
            data = {
                'status': False,
                'msg': 'Activity is either missing or you do not have permissions'
            }
        else:
            data = {
                'status': True,
                'link': activity.evenote_publish_note()
            }
        return self.render_json_response(data)



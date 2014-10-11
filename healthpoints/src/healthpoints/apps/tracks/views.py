from django.shortcuts import render
from django.views.generic import TemplateView

from braces import views


class MainView(TemplateView):
    template_name = "index.html"

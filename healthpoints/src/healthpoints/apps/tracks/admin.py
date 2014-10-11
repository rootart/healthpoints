from django.contrib.gis import admin


from .models import Activity

class ActivityAdmin(admin.GeoModelAdmin):
    pass


admin.site.register(Activity, ActivityAdmin)


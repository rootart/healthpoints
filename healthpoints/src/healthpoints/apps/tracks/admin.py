from django.contrib.gis import admin


from .models import Activity, ActivityFBActions


class ActivityFBActionAdminInline(admin.StackedInline):
    model = ActivityFBActions


class ActivityAdmin(admin.GeoModelAdmin):
    list_display = ('__unicode__', 'fb_id', 'note_url')
    inlines = [ActivityFBActionAdminInline,]


class ActivityFBActionAdmin(admin.ModelAdmin):
    list_display = ('activity_type', 'activity')


admin.site.register(Activity, ActivityAdmin)
admin.site.register(ActivityFBActions, ActivityFBActionAdmin)


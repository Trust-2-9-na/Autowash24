from django.contrib import admin
from .models import UserProfile, SensorData, SystemStatus, SystemSettings

class SensorDataAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'hands_washed', 'water_dispensed_ml', 'current_water_volume_ml', 'ir_sensor_detected')  # Updated field names
    list_filter = ('timestamp',)  # Update this as needed
    search_fields = ('timestamp', 'hands_washed', 'water_dispensed_ml', 'current_water_volume_ml', 'ir_sensor_detected')  # Updated field names

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'address', 'phone_number')
    search_fields = ('user__username', 'address', 'phone_number')

class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ('flow_speed', 'duration')  

class SystemStatusAdmin(admin.ModelAdmin):
    list_display = ('user', 'water_level', 'ultrasonic_distance_cm', 'operational_state', 'anomaly_detected', 'anomaly_description')  # Updated field names
    list_editable = ('water_level', 'operational_state', 'anomaly_detected', 'anomaly_description')  # Updated field names
    actions = []  

admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(SensorData, SensorDataAdmin)
admin.site.register(SystemStatus, SystemStatusAdmin)
admin.site.register(SystemSettings, SystemSettingsAdmin)

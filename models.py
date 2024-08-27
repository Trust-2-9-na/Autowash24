from PIL import Image
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100, default='Unknown')
    last_name = models.CharField(max_length=100, default='Unknown')
    email = models.EmailField(default='unknown')
    address = models.CharField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics', blank=True, null=True)
    def __str__(self):
        if self.user:
            return self.user.username
        else:
            return "No associated user"

    @property
    def username(self):
        return self.user.username

class SensorData(models.Model):
    timestamp = models.DateTimeField(default=timezone.now)
    hands_washed = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    water_dispensed_ml = models.FloatField(default=0.0)
    current_water_volume_ml = models.FloatField()
    ir_sensor_detected = models.BooleanField(default=False)
    last_known_volume_ml = models.FloatField(default=0.0)  # New field to track the last known volume

    def __str__(self):
        return (f"{self.timestamp} - Hands: {self.hands_washed}, Water Dispensed: {self.water_dispensed_ml}ml, "
                f"Current Water Volume: {self.current_water_volume_ml}ml, IR Detected: {self.ir_sensor_detected}")

@receiver(post_save, sender=SensorData)
def update_water_dispensed(sender, instance, **kwargs):
    try:
        # Get the previous reading
        previous_reading = SensorData.objects.filter(timestamp__lt=instance.timestamp).order_by('-timestamp').first()

        if previous_reading:
            # Calculate the water dispensed only if the volume decreases
            if previous_reading.current_water_volume_ml > instance.current_water_volume_ml:
                water_dispensed = previous_reading.current_water_volume_ml - instance.current_water_volume_ml
                instance.water_dispensed_ml = water_dispensed
            else:
                # If water is added, set water_dispensed_ml to 0
                instance.water_dispensed_ml = 0.0

            # Update the last known volume
            instance.last_known_volume_ml = instance.current_water_volume_ml
            instance.save(update_fields=['water_dispensed_ml', 'last_known_volume_ml'])
        else:
            # Handle case where there is no previous reading
            instance.water_dispensed_ml = 0.0
            instance.last_known_volume_ml = instance.current_water_volume_ml
            instance.save(update_fields=['water_dispensed_ml', 'last_known_volume_ml'])
    except Exception as e:
        # Log the error or handle it as needed
        print(f"Error updating water dispensed: {e}")


from django.db import models

DURATION_CHOICES = [
    (5000, '5 seconds'),
    (10000, '10 seconds'),
    (15000, '15 seconds'),
    (20000, '20 seconds'),
    (25000, '25 seconds'),
    (30000, '30 seconds'),
    (35000, '35 seconds'),
    (40000, '40 seconds'),
]

class SystemSettings(models.Model):
    flow_speed = models.IntegerField(
        choices=[(0, '0'), (64, '64'), (85, '85'), (100, '100'), (120, '120'), (128, '128'), (160, '160'), (190, '190'), (220, '220'), (240, '240'), (255, '255')],
        verbose_name="Flow Speed",
        help_text="Select a flow speed from the predefined choices."
    )
    duration = models.IntegerField(
        choices=DURATION_CHOICES,
        verbose_name="Duration",
        help_text="Select a duration in milliseconds from the predefined choices.",
        default=5000  # Default value
    )
    
    def set_flow_speed(self, speed):
        valid_speeds = [0, 64, 85, 100, 120, 128, 160, 190, 220, 240, 255]
        if speed in valid_speeds:
            self.flow_speed = speed
        else:
            raise ValueError("Invalid flow speed")

    def set_duration(self, duration):
        valid_durations = [5000, 10000, 15000, 20000, 25000, 30000, 35000, 40000]
        if duration in valid_durations:
            self.duration = duration
        else:
            raise ValueError("Invalid duration. Must be one of: 5000, 10000, 15000, 20000, 25000, 30000, 35000, 40000 milliseconds")

    def apply_settings(self):
        # Convert duration from milliseconds to seconds
        duration_in_seconds = self.duration / 1000
        # Code to send settings to hardware
        print(f"Applying settings: Flow Speed = {self.flow_speed}, Duration = {duration_in_seconds} seconds")


class SystemStatus(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    water_level = models.FloatField(default=0.0)
    ultrasonic_distance_cm = models.FloatField(null=True, blank=True)
    operational_state = models.CharField(
        max_length=50,
        choices=[
            ('Normal', 'Normal'),
            ('Maintenance Required', 'Maintenance Required'),
        ],
        null=True,
        blank=True
    )
    anomaly_detected = models.BooleanField(default=False)
    anomaly_description = models.TextField(null=True, blank=True)

    def __str__(self):
        return (f"{self.user.username} Status - Water Level: {self.water_level}cm, "
                f"Ultrasonic Distance: {self.ultrasonic_distance_cm}cm, "
                f"Operational State: {self.operational_state}, "
                f"Anomaly: {'Yes' if self.anomaly_detected else 'No'}, "
                f"Description: {self.anomaly_description}")

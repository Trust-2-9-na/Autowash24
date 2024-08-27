from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from .forms import UserProfileForm, SystemStatusForm, SignupForm
from .models import SystemSettings, SystemStatus, SensorData, UserProfile
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.views import LoginView
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import SensorData, SystemSettings
from .serializers import SensorDataSerializer, SystemSettingsSerializer
from rest_framework import viewsets
from .models import SensorData, SystemSettings, SystemStatus, UserProfile
from .serializers import SensorDataSerializer, SystemSettingsSerializer, SystemStatusSerializer, UserProfileSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
import logging
from django.utils import timezone
import json
from django.db.models import Avg
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
import logging
from .models import SensorData, SystemSettings, SystemStatus, UserProfile
from .serializers import SensorDataSerializer, SystemSettingsSerializer, SystemStatusSerializer, UserProfileSerializer
from datetime import timedelta
from rest_framework import status
from rest_framework.decorators import api_view



logger = logging.getLogger(__name__)

class UnifiedAPIView(APIView):
    def get(self, request, *args, **kwargs):
        # Retrieve data from all models
        sensor_data = SensorData.objects.all()
        system_status = SystemStatus.objects.all()
        system_settings = SystemSettings.objects.all()

        # Serialize the data
        sensor_data_serializer = SensorDataSerializer(sensor_data, many=True)
        system_status_serializer = SystemStatusSerializer(system_status, many=True)
        system_settings_serializer = SystemSettingsSerializer(system_settings, many=True)

        # Combine the serialized data
        combined_data = {
            'sensor_data': sensor_data_serializer.data,
            'system_status': system_status_serializer.data,
            'system_settings': system_settings_serializer.data,
        }

        return Response(combined_data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        # Handle posting data to SensorData and SystemStatus
        sensor_data_serializer = SensorDataSerializer(data=request.data.get('sensor_data'))
        system_status_serializer = SystemStatusSerializer(data=request.data.get('system_status'))

        if sensor_data_serializer.is_valid():
            sensor_data_serializer.save()
        else:
            return Response(sensor_data_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if system_status_serializer.is_valid():
            system_status_serializer.save()
        else:
            return Response(system_status_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response({'message': 'Data saved successfully'}, status=status.HTTP_201_CREATED)

    def put(self, request, *args, **kwargs):
        # Handle updating system settings
        settings = SystemSettings.objects.first()
        if settings is None:
            return Response({"detail": "No settings found to update."}, status=status.HTTP_404_NOT_FOUND)

        serializer = SystemSettingsSerializer(settings, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            # Send the index values to the hardware
            speed_index = serializer.validated_data.get('flow_speed')
            time_index = serializer.validated_data.get('duration')
            send_settings_to_hardware(speed_index, time_index)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def send_settings_to_hardware(speed_index, time_index):
    # Code to send the index values to the hardware
    # This could be through a serial connection, HTTP request, etc.
    pass


class SensorDataViewSet(viewsets.ModelViewSet):
    queryset = SensorData.objects.all()
    serializer_class = SensorDataSerializer

class SystemSettingsViewSet(viewsets.ModelViewSet):
    serializer_class = SystemSettingsSerializer

    def get_queryset(self):
        user = self.request.user
        return SystemSettings.objects.filter(user=user)

    def get_object(self):
        user = self.request.user
        return SystemSettings.objects.get(user=user)

class SystemStatusViewSet(viewsets.ModelViewSet):
    queryset = SystemStatus.objects.all()
    serializer_class = SystemStatusSerializer

class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer

class SensorDataList(APIView):
    def get(self, request, *args, **kwargs):
        sensor_data = SensorData.objects.all()
        serializer = SensorDataSerializer(sensor_data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = SensorDataSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_current_settings(request):
    """
    Retrieve the current system settings.
    """
    try:
        settings = SystemSettings.objects.first()
        if settings is not None:
            serializer = SystemSettingsSerializer(settings)
            return Response(serializer.data)
        else:
            return Response({"detail": "No settings found."}, status=status.HTTP_404_NOT_FOUND)
    except SystemSettings.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
def update_settings(request):
    """
    Update the system settings.
    """
    settings = SystemSettings.objects.first()
    if settings is None:
        return Response({"detail": "No settings found to update."}, status=status.HTTP_404_NOT_FOUND)
    
    serializer = SystemSettingsSerializer(data=request.data)
    if serializer.is_valid():
        # Validate and update flow speed and duration using model methods
        settings.set_flow_speed(serializer.validated_data['flow_speed'])
        settings.set_duration(serializer.validated_data['duration'])
        settings.save()
        settings.apply_settings()  # Send settings to the hardware
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class SystemStatusList(APIView):
    def get(self, request, *args, **kwargs):
        status_data = SystemStatus.objects.all()
        serializer = SystemStatusSerializer(status_data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = SystemStatusSerializer(data=request.data)
        if serializer.is_valid():
            # Check if an entry for the user already exists and update it if it does
            user = request.user
            if SystemStatus.objects.filter(user=user).exists():
                system_status = SystemStatus.objects.get(user=user)
                serializer = SystemStatusSerializer(system_status, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data, status=status.HTTP_200_OK)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                # Create a new entry if it does not exist
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserProfileList(APIView):
    def get(self, request, *args, **kwargs):
        profiles = UserProfile.objects.all()
        serializer = UserProfileSerializer(profiles, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        user = request.user
        data = request.data.copy()
        data['user'] = user.id  # Ensure the user field is set
        serializer = UserProfileSerializer(data=data)
        if serializer.is_valid():
            # Check if a profile for the user already exists and update it if it does
            if UserProfile.objects.filter(user=user).exists():
                profile = UserProfile.objects.get(user=user)
                serializer = UserProfileSerializer(profile, data=data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data, status=status.HTTP_200_OK)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                # Create a new profile if it does not exist
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomLoginView(LoginView):
    template_name = 'autowash/login.html'
    redirect_authenticated_user = True


def calculate_hourly_averages():
    now = timezone.now()
    one_hour_ago = now - timedelta(hours=1)
    
    # Query data from the past hour
    recent_data = SensorData.objects.filter(timestamp__range=(one_hour_ago, now))
    
    if recent_data.exists():
        avg_hands_washed = recent_data.aggregate(Avg('hands_washed'))['hands_washed__avg']
        avg_water_dispensed = recent_data.aggregate(Avg('water_dispensed_ml'))['water_dispensed_ml__avg']
        
        # Round to two decimal places
        avg_hands_washed = round(avg_hands_washed, 1) if avg_hands_washed is not None else 0
        avg_water_dispensed = round(avg_water_dispensed, 1) if avg_water_dispensed is not None else 0
    else:
        avg_hands_washed = 0
        avg_water_dispensed = 0

    return avg_hands_washed, avg_water_dispensed


def average_sensor_view(request):
    avg_hands_washed, avg_water_dispensed = calculate_hourly_averages()
    
    context = {
        'avg_hands_washed': avg_hands_washed,
        'avg_water_dispensed': avg_water_dispensed,
    }
    
    return render(request, 'average_sensor.html', context)

@login_required
def contact(request):
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        
        if not name or not email or not message:
            messages.error(request, "All fields are required.")
            return redirect('contact')
        
        try:
            send_mail(
                f"New Contact Message from {name}",
                message,
                email,
                ['tnachokwe@gmail.com'],  
            )
            messages.success(request, "Your message has been sent successfully.")
        except Exception as e:
            messages.error(request, "Failed to send your message. Please check your network connection and try again.")
        
        return redirect('contact')
    
    return render(request, 'contact.html')
@login_required
def index(request):
    return render(request, 'index.html')
@login_required
def about(request):
    return render(request, 'about.html')
@login_required
def help(request):
    return render(request, 'help.html')

@login_required
def sensor_charts(request):
    sensor_data = SensorData.objects.all()
    system_settings = SystemSettings.objects.all()
    sensor_data_serializer = SensorDataSerializer(sensor_data, many=True)
    system_settings_serializer = SystemSettingsSerializer(system_settings, many=True)
    sensor_data_json = json.dumps(sensor_data_serializer.data)
    system_settings_json = json.dumps(system_settings_serializer.data)

    context = {
        'sensor_data_json': sensor_data_json,
        'system_settings_json': system_settings_json,
    }
    return render(request, 'sensor_charts.html', context)

from django.http import JsonResponse
import requests

@login_required
def system_settings_view(request):
    if request.method == 'GET':
        settings = SystemSettings.objects.first()
        if settings:
            # Convert duration from milliseconds to seconds for display
            duration_seconds = settings.duration / 1000 if settings.duration else 0
            
            serializer = SystemSettingsSerializer(settings)
            context = {
                'settings': serializer.data,
                'flow_speeds': [0, 64, 85, 100, 120, 128, 160, 190, 220, 240, 255],
                'durations': [{'ms': 5000, 'sec': 5}, {'ms': 10000, 'sec': 10}, {'ms': 15000, 'sec': 15}, {'ms': 20000, 'sec': 20}, {'ms': 25000, 'sec': 25}, {'ms': 30000, 'sec': 30}, {'ms': 35000, 'sec': 35}, {'ms': 40000, 'sec': 40}],  # Durations in milliseconds and seconds
                'duration_seconds': duration_seconds
            }
            return render(request, 'system_settings.html', context)
        else:
            return render(request, 'system_settings.html', {'error': 'No settings found.'})
    elif request.method == 'POST':
        settings = SystemSettings.objects.first()
        if settings is None:
            return JsonResponse({"detail": "No settings found to update."}, status=status.HTTP_404_NOT_FOUND)
        
        # Convert duration from seconds to milliseconds before saving
        duration_in_milliseconds = int(request.POST.get('duration')) * 1000
        request.POST = request.POST.copy()
        request.POST['duration'] = duration_in_milliseconds

        serializer = SystemSettingsSerializer(data=request.POST)
        if serializer.is_valid():
            settings.set_flow_speed(serializer.validated_data['flow_speed'])
            settings.set_duration(serializer.validated_data['duration'])
            settings.save()
            settings.apply_settings()
            messages.success(request, "Settings updated successfully.")
            return redirect('system_settings_view')
        else:
            messages.error(request, "Failed to update settings. Please correct the errors below.")
            return render(request, 'system_settings.html', {
                'settings': serializer.data,
                'flow_speeds': [0, 64, 85, 100, 120, 128, 160, 190, 220, 240, 255],
                'durations': [{'ms': 5000, 'sec': 5}, {'ms': 10000, 'sec': 10}, {'ms': 15000, 'sec': 15}, {'ms': 20000, 'sec': 20}, {'ms': 25000, 'sec': 25}, {'ms': 30000, 'sec': 30}, {'ms': 35000, 'sec': 35}, {'ms': 40000, 'sec': 40}],  # Durations in milliseconds and seconds
                'errors': serializer.errors
            })

@login_required
def sensor_data(request):
    sensor_data = SensorData.objects.all()
    return render(request, 'sensor_data.html', {'sensor_data': sensor_data})

@login_required
def system_status(request):
    try:
        system_status = SystemStatus.objects.get(user=request.user)
    except SystemStatus.DoesNotExist:
        system_status = SystemStatus.objects.create(
            user=request.user,
            water_level =0.0,  # Updated field
            ultrasonic_distance_cm=0.0,  # Added field
            operational_state="Normal",
            anomaly_detected=False,
            anomaly_description=""
        )
        messages.info(request, 'Default system status has been created for your account.')

    if request.method == 'POST':
        form = SystemStatusForm(request.POST, instance=system_status)
        if form.is_valid():
            form.save()
            messages.success(request, 'System status updated successfully.')
            return redirect('system-status')
    else:
        form = SystemStatusForm(instance=system_status)

    return render(request, 'system_status.html', {'form': form, 'system_status': system_status})


@login_required
def user_profile(request):
    user = request.user
    user_profile, created = UserProfile.objects.get_or_create(user=user)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            user.save()
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('view-profile')
    else:
        form = UserProfileForm(instance=user_profile)

    return render(request, 'user_profile.html', {'form': form})

@login_required
def view_profile(request):
    user = request.user
    user_profile, created = UserProfile.objects.get_or_create(user=user)
    return render(request, 'view_profile.html', {'user_profile': user_profile})


@login_required
def view_profile(request):
    user_profile = get_object_or_404(UserProfile, user=request.user)
    return render(request, 'view_profile.html', {'user_profile': user_profile})

def landing_page(request):
    if request.session.get('visited_website'):
        welcome_back_message = "Welcome back!"
        request.session['visited_website'] = False
    else:
        welcome_back_message = None
    
    return render(request, 'landing.html', {'welcome_back_message': welcome_back_message})
@login_required
def signout(request):
    if request.method == 'POST':
        logout(request)
        request.session['visited_website'] = True
        return redirect('login')
    else:
        return redirect('landing')                

def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = SignupForm()
    return render(request, 'signup.html', {'form': form})
@login_required
def change_account(request):
    if request.method == 'POST':
        return redirect('home')  
    return render(request, 'change_account.html')

def stay_logged_out(request):
    return render(request,'landing.html')
            
def about_land(request):
    return render(request, 'about_land.html')
def help_land(request):
    return render(request, 'help_land.html')
def contact_land(request):
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        
        if not name or not email or not message:
            messages.error(request, "All fields are required.")
            return redirect('contact')
        
        try:
            send_mail(
                f"New Contact Message from {name}",
                message,
                email,
                ['tnachokwe@gmail.com'],  
            )
            messages.success(request, "Your message has been sent successfully.")
        except Exception as e:
            messages.error(request, "Failed to send your message. Please check your network connection and try again.")
        
        return redirect('contact')
    
    return render(request, 'contact_land.html')


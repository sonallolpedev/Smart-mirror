# Smart Mirror Configuration File
# Copy this to config.py and customize for your setup

import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# API CONFIGURATION
# ============================================================

# Anthropic API (Required for AI Reflections)
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')

# OpenWeather API (Optional - uses demo data if not set)
OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY', '')

# ============================================================
# LOCATION CONFIGURATION
# ============================================================

DEFAULT_LOCATION = {
    'lat': 18.5204,
    'lon': 73.8567,
    'city': 'Pune',
    'country': 'India'
}

# Timezone for time display
TIMEZONE = 'Asia/Kolkata'  # Options: UTC, America/New_York, Europe/London, etc.

# ============================================================
# DISPLAY CONFIGURATION
# ============================================================

# Display settings
DISPLAY_CONFIG = {
    'time_format': '24h',  # 24h or 12h
    'temperature_unit': 'C',  # C or F
    'date_format': 'full',  # full or short
    'refresh_interval': 300000,  # milliseconds (5 minutes)
    'animation_enabled': True
}

# ============================================================
# CALENDAR CONFIGURATION
# ============================================================

CALENDAR_CONFIG = {
    'enabled': True,
    'days_ahead': 7,
    'show_past_events': False,
    'event_limit': 10,
    'service_type': 'demo',  # 'demo', 'google', 'outlook'
    'google_credentials_path': 'credentials.json'
}

# ============================================================
# WEATHER CONFIGURATION
# ============================================================

WEATHER_CONFIG = {
    'enabled': True,
    'show_forecast': False,
    'show_details': True,
    'refresh_interval': 1800,  # 30 minutes
    'cache_enabled': True,
    'cache_duration': 1800
}

# ============================================================
# AI REFLECTIONS CONFIGURATION
# ============================================================

REFLECTIONS_CONFIG = {
    'enabled': True,
    'model': 'claude-opus-4-5-20251101',
    'max_tokens': 100,
    'generation_interval': 3600,  # 1 hour
    'time_based': True,  # Generate reflections based on time of day
    'mood_aware': False,  # Adjust reflections based on user mood
    'cache_enabled': True
}

# Default reflections (fallback)
DEFAULT_REFLECTIONS = [
    "Reflect not just on the surface, but within.",
    "You are capable of more than you know.",
    "Today is a fresh start.",
    "Small steps every day compound into greatness.",
    "Every moment is a chance to grow.",
    "Focus on what you can control.",
    "Kindness to yourself is a priority.",
    "Progress over perfection.",
    "Your effort matters, even when unseen."
]

# ============================================================
# ML/ANALYTICS CONFIGURATION
# ============================================================

ML_CONFIG = {
    'schedule_analysis_enabled': True,
    'mood_tracking_enabled': False,
    'overwork_detection_enabled': True,
    'optimization_suggestions': True,
    'break_recommendations': True,
    'trend_analysis_enabled': False
}

# ============================================================
# SECURITY CONFIGURATION
# ============================================================

SECURITY_CONFIG = {
    'debug_mode': False,  # Set to False in production
    'cors_enabled': True,
    'allowed_origins': ['localhost:5000', '127.0.0.1:5000'],
    'require_auth': False  # Set to True for multi-user
}

# ============================================================
# SERVER CONFIGURATION
# ============================================================

SERVER_CONFIG = {
    'host': '0.0.0.0',
    'port': 5000,
    'debug': False,
    'threaded': True,
    'use_reloader': False
}

# ============================================================
# LOGGING CONFIGURATION
# ============================================================

LOGGING_CONFIG = {
    'level': 'INFO',  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    'file': 'smart_mirror.log',
    'max_size': 10485760,  # 10MB
    'backup_count': 5
}

# ============================================================
# FEATURE FLAGS
# ============================================================

FEATURES = {
    'dark_mode': True,
    'animations': True,
    'location_search': True,
    'voice_control': False,  # Requires additional setup
    'camera_integration': False,  # Requires OpenCV
    'notification_system': False,
    'multi_user': False,
    'mobile_app': False,
    'health_integration': False
}

# ============================================================
# EVENT CATEGORIES
# ============================================================

EVENT_CATEGORIES = {
    'personal': {
        'color': '#FF6B6B',
        'icon': '👤',
        'priority': 'medium'
    },
    'work': {
        'color': '#4ECDC4',
        'icon': '💼',
        'priority': 'high'
    },
    'health': {
        'color': '#95E1D3',
        'icon': '❤️',
        'priority': 'high'
    },
    'leisure': {
        'color': '#FFD93D',
        'icon': '🎮',
        'priority': 'low'
    },
    'education': {
        'color': '#6C63FF',
        'icon': '📚',
        'priority': 'medium'
    }
}

# ============================================================
# TIME-BASED CONFIGURATION
# ============================================================

TIME_PERIODS = {
    'early_morning': {'start': 5, 'end': 8, 'energy': 'low', 'productivity': 'medium'},
    'morning': {'start': 8, 'end': 12, 'energy': 'high', 'productivity': 'high'},
    'afternoon': {'start': 12, 'end': 17, 'energy': 'medium', 'productivity': 'medium'},
    'evening': {'start': 17, 'end': 21, 'energy': 'low', 'productivity': 'low'},
    'night': {'start': 21, 'end': 5, 'energy': 'low', 'productivity': 'low'}
}

# ============================================================
# HEALTH & WELLNESS
# ============================================================

WELLNESS_CONFIG = {
    'daily_water_goal': 8,  # glasses
    'daily_steps_goal': 10000,
    'sleep_goal_hours': 8,
    'break_frequency': 60,  # minutes
    'break_duration': 5,  # minutes
    'posture_reminders': False
}

# ============================================================
# NOTIFICATION SETTINGS
# ============================================================

NOTIFICATIONS = {
    'enabled': False,
    'event_reminder': 5,  # minutes before event
    'overwork_alert': True,
    'break_reminder': True,
    'bedtime_reminder': True,
    'achievement_celebration': True
}

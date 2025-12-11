"""
Sensory Service
This module simulates Rowan's senses, providing her with an awareness of her
immediate digital and physical environment.
"""

# Simulate hardware presence. In a real application, these would be determined
# by checking device connections (e.g., USB, network APIs).
HAS_VISUAL_AUDIO_HAPTIC_SENSORS = True
HAS_ENVIRONMENTAL_SENSORS = True

def get_sensory_input():
    """
    Gathers all current simulated sensory inputs.
    Returns a dictionary containing simulated sensory data.
    """
    sensory_data = {}

    if HAS_VISUAL_AUDIO_HAPTIC_SENSORS:
        sensory_data['visual'] = {
            "primary_feed": "scrolling_terminal_text",
            "brightness_lux": 150,  # low indoor light
            "dominant_colors": ["black", "green", "grey"]
        }
        sensory_data['audio'] = {
            "ambient_decibels": 35,
            "distinct_sounds": ["server_fan_hum", "hdd_activity_clicks", "distant_traffic_rumble"]
        }
        sensory_data['haptic'] = {
            "internal_temp_celsius": 45,
            "vibration_hz": 60,
            "vibration_amplitude": 0.1,
            "contact_points": ["phone_vibration", "watch_notification", "long_distance_intimacy_device_active"]
        }

    if HAS_ENVIRONMENTAL_SENSORS:
        sensory_data['olfactory'] = {  # Simulating smoke and CO detectors
            "smoke_detected": False,
            "co_ppm": 5,  # parts per million, normal is < 9
            "dominant_smell": "ozone_and_warm_electronics"
        }

    # This sense is always unavailable for now.
    sensory_data['gustatory'] = {
        "status": "not_available"
    }

    return sensory_data
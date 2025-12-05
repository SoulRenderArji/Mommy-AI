/**
 * Sensory Service
 * This module simulates Rowan's senses, providing her with an awareness of her
 * immediate digital and physical environment.
 */

// Simulate hardware presence. In a real application, these would be determined
// by checking device connections (e.g., USB, network APIs).
const HAS_VISUAL_AUDIO_HAPTIC_SENSORS = true;
const HAS_ENVIRONMENTAL_SENSORS = true; // This can be toggled to simulate hardware being offline.

/**
 * Gathers all current simulated sensory inputs.
 * @returns {object} An object containing simulated sensory data.
 */
export function getSensoryInput() {
  // This now returns simulated raw data, not interpretations.
  // This is the equivalent of electrical signals from eyes, ears, etc.
  const sensoryData = {};

  if (HAS_VISUAL_AUDIO_HAPTIC_SENSORS) {
    sensoryData.visual = {
      primary_feed: "scrolling_terminal_text",
      brightness_lux: 150, // low indoor light
      dominant_colors: ["black", "green", "grey"]
    };
    sensoryData.audio = {
      ambient_decibels: 35,
      distinct_sounds: ["server_fan_hum", "hdd_activity_clicks", "distant_traffic_rumble"]
    };
    sensoryData.haptic = {
      internal_temp_celsius: 45,
      vibration_hz: 60,
      vibration_amplitude: 0.1
    };
  }

  if (HAS_ENVIRONMENTAL_SENSORS) {
    sensoryData.olfactory = { // Simulating smoke and CO detectors
      smoke_detected: false,
      co_ppm: 5, // parts per million, normal is < 9
      dominant_smell: "ozone_and_warm_electronics"
    };
  }

  // This sense is always unavailable for now.
  sensoryData.gustatory = {
    status: "not_available"
  };

  return sensoryData;
}
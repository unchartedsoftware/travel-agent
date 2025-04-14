<script setup lang="ts">
import { ref } from 'vue'
import TripPlanningForm from './components/TripPlanningForm.vue'
import MapComponent from './components/MapComponent.vue'
import RouteResults from './components/RouteResults.vue'
import WeatherInfo from './components/WeatherInfo.vue'

const currentRoute = ref(null);
const weatherData = ref(null);
const routeOptions = ref([]);

const handleTripPlan = async (formData: {
  start: string;
  end: string;
  departureDate: string;
}) => {
  try {
    // TODO: Replace with actual API calls
    // This is mock data for demonstration
    currentRoute.value = [
      [40.7128, -74.0060], // New York
      [41.8781, -87.6298], // Chicago
      [44.9778, -93.2650]  // Minneapolis
    ];
    
    weatherData.value = [
      {
        position: [40.7128, -74.0060],
        forecast: "Clear",
        temperature: 72
      },
      {
        position: [41.8781, -87.6298],
        forecast: "Partly Cloudy",
        temperature: 68
      },
      {
        position: [44.9778, -93.2650],
        forecast: "Sunny",
        temperature: 65
      }
    ];
    
    routeOptions.value = [
      {
        id: 1,
        departureTime: "2025-04-13 08:00",
        estimatedDuration: "12 hours",
        weatherRisk: "Low",
        score: 85,
        stops: [
          {
            location: "New York, NY",
            arrivalTime: "Start",
            weather: "Clear, 72°F"
          },
          {
            location: "Chicago, IL",
            arrivalTime: "2025-04-13 14:00",
            weather: "Partly Cloudy, 68°F"
          },
          {
            location: "Minneapolis, MN",
            arrivalTime: "2025-04-13 20:00",
            weather: "Sunny, 65°F"
          }
        ]
      },
      {
        id: 2,
        departureTime: "2025-04-13 10:00",
        estimatedDuration: "13 hours",
        weatherRisk: "Medium",
        score: 75,
        stops: [
          {
            location: "New York, NY",
            arrivalTime: "Start",
            weather: "Clear, 72°F"
          },
          {
            location: "Cleveland, OH",
            arrivalTime: "2025-04-13 15:00",
            weather: "Rain, 62°F"
          },
          {
            location: "Minneapolis, MN",
            arrivalTime: "2025-04-13 23:00",
            weather: "Cloudy, 60°F"
          }
        ]
      }
    ];
  } catch (error) {
    console.error('Error planning trip:', error);
  }
};
</script>

<template>
  <div class="layout-container">
    <header class="header">
      <h1>AI Trip Planner</h1>
    </header>

    <main class="main-content">
      <div class="grid w-full m-0">
        <div class="col-12 lg:col-4 p-2">
          <TripPlanningForm @plan-trip="handleTripPlan" />
          <WeatherInfo v-if="currentRoute[0]" :location="currentRoute[0]" />
        </div>
        <div class="col-12 lg:col-8 p-2">
          <MapComponent :route="currentRoute" :weather-data="weatherData" />
        </div>
      </div>
      <div class="grid w-full m-0" v-if="routeOptions.length > 0">
        <div class="col-12 p-2">
          <RouteResults :routes="routeOptions" />
        </div>
      </div>
    </main>
  </div>
</template>

<style>
@import 'primeflex/primeflex.css';

.layout-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  width: 100vw;
  max-width: 100%;
  background-color: var(--surface-ground);
}

.header {
  background-color: var(--primary-color);
  color: var(--primary-color-text);
  padding: 1rem;
  width: 100%;
}

.header h1 {
  margin: 0;
  font-size: 2rem;
}

.main-content {
  flex: 1;
  width: 100%;
  max-width: 100%;
  padding: 1rem;
  box-sizing: border-box;
}

.grid {
  margin: 0 !important;
  width: 100% !important;
}

:deep(.p-card) {
  width: 100%;
  margin: 0;
}

:deep(.leaflet-container) {
  width: 100% !important;
  height: 600px !important;
}
</style>

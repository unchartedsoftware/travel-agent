<script setup lang="ts">
import { ref } from 'vue'
import TripPlanningForm from './components/TripPlanningForm.vue'
import MapComponent from './components/MapComponent.vue'
import RouteResults from './components/RouteResults.vue'
import WeatherInfo from './components/WeatherInfo.vue'
import ProgressSpinner from 'primevue/progressspinner'
import AIMessages from './components/AIMessages.vue'
import type { WeatherStop, TripFormData, RouteOption } from './models/types'
import { openweathermapApiKey } from './utilities/weather'

const API_BASE_URL = 'http://localhost:8000';

const currentRoute = ref<[number, number][]>([]);
const weatherData = ref<Array<{position: [number, number], forecast: string, temperature: number}> | null>(null);
const routeOptions = ref<RouteOption[]>([]);
const isLoading = ref(false);
const aiMessages = ref<string[]>([]);

const handleTripPlan = async (formData: TripFormData) => {
  isLoading.value = true;
  aiMessages.value = [];
  routeOptions.value = [];
  weatherData.value = null;
  currentRoute.value = [];
  try {
    // Make both API calls in parallel
    const [aiResponse] = await Promise.all([
      fetch(`${API_BASE_URL}/api/plan-trip`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          start: formData.start,
          end: formData.end,
          departure_time: formData.departure_time
        })
      }),
    ]);

    if (!aiResponse.ok) {
      throw new Error('Failed to fetch route options or AI suggestions');
    }

    const [aiData] = await Promise.all([
      aiResponse.json()
    ]);

    // Update route display with the first route option's coordinates
    if (aiData?.route_options?.[0]) {
      currentRoute.value = aiData.route_options[0].coordinates;

      // Transform weather data for display using the stop's actual coordinates
      weatherData.value = aiData.route_options[0].stops.map((stop: WeatherStop) => ({
        position: stop.coordinates as [number, number],
        forecast: stop.weather.split(',')[0],
        temperature: parseInt(stop.weather.split(',')[1]),
        location: stop.location,
        arrivalTime: stop.arrival_time
      }));
    }

    // routeOptions.value = routeData;
    routeOptions.value = aiData.route_options;
    aiMessages.value = aiData.ai_messages_content;

  } catch (error) {
    console.error('Error planning trip:', error);
  } finally {
    isLoading.value = false;
  }
};
</script>

<template>
  <div class="layout-container">
    <header class="header">
      <h1>Weather Travel Agent</h1>
    </header>

    <main class="main-content">
      <div class="grid w-full m-0">
        <div class="col-12 lg:col-4 p-2">
          <TripPlanningForm @plan-trip="handleTripPlan" />
          <WeatherInfo v-if="weatherData && weatherData.length > 0" :weather="weatherData[0]" />
        </div>
        <div class="col-12 lg:col-8 p-2">
          <div class="relative">
            <MapComponent :route="currentRoute" :weather-data="weatherData" :weatherApiKey="openweathermapApiKey" />
            <div v-if="isLoading" class="loading-overlay">
              <ProgressSpinner />
              <div class="loading-text">Planning your trip...</div>
            </div>
          </div>
        </div>
      </div>
      <div class="grid w-full m-0" v-if="routeOptions.length > 0">
        <div class="col-12 p-2">
          <RouteResults :routes="routeOptions" />
        </div>
        <div class="col-12 p-2">
          <AIMessages :messages="aiMessages" />
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
  font-size: 1.6rem; /* Reduced from 2rem */
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

.relative {
  position: relative;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  z-index: 1000;
}

.loading-text {
  color: var(--primary-color);
  font-size: 0.96rem; /* Reduced from 1.2rem */
  font-weight: 500;
}

.results-container {
  display: flex;
  gap: 2rem;
  margin-top: 2rem;
}

.map-container {
  flex: 1;
  min-width: 0;
}

.info-container {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
</style>

<script setup lang="ts">
import { ref } from 'vue'
import TripPlanningForm from './components/TripPlanningForm.vue'
import MapComponent from './components/MapComponent.vue'
import RouteResults from './components/RouteResults.vue'
import WeatherInfo from './components/WeatherInfo.vue'
import type { WeatherStop, TripFormData, RouteOption } from './models/types'

const currentRoute = ref<[number, number][] | null>(null);
const weatherData = ref<Array<{position: [number, number], forecast: string, temperature: number}> | null>(null);
const routeOptions = ref<RouteOption[]>([]);

const handleTripPlan = async (formData: TripFormData) => {
  try {
    const response = await fetch('http://localhost:8000/api/plan-trip', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        start: formData.start,
        end: formData.end,
        departure_time: formData.departureDate
      })
    });

    if (!response.ok) {
      throw new Error('Failed to fetch route options');
    }

    const data = await response.json();

    // Update route display with the first route option's coordinates
    if (data[0]) {
      currentRoute.value = data[0].coordinates;

      // Transform weather data for display, matching each stop with the next coordinate
      // (since weather data is for the destination of each leg)
      weatherData.value = data[0].stops.map((stop: WeatherStop, index: number) => ({
        position: data[0].coordinates[index + 1] as [number, number],  // Use next coordinate since weather is for destination
        forecast: stop.weather.split(',')[0],
        temperature: parseInt(stop.weather.split(',')[1])
      }));
    }

    routeOptions.value = data;

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
          <WeatherInfo v-if="currentRoute && currentRoute.length > 0" :location="currentRoute[0]" />
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

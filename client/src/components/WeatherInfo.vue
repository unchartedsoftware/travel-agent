<template>
    <div v-if="weather">
        <h3>🌤️ Weather for {{ weather.name }}</h3>
        <p><strong>Temperature:</strong> {{ weather.main.temp }}°C</p>
        <p><strong>Condition:</strong> {{ weather.weather[0].description }}</p>
        <p><strong>Humidity:</strong> {{ weather.main.humidity }}%</p>
        <p><strong>Wind:</strong> {{ weather.wind.speed }} m/s</p>
    </div>
    <div v-else-if="loading">
        <p>Loading weather data...</p>
    </div>
    <div v-else>
        <p>Click a location on the map to get weather info.</p>
    </div>
</template>
  
  <script setup lang="ts">
  import { ref, watch } from 'vue';
  import type { WeatherStop } from '../models/types';
  import { getCurrentForecast } from '../utilities/weather';
  
  const props = defineProps<{
    weather: WeatherStop;
  }>();
  
  const weather = ref<{
    name: string;
    main: {
      temp: number;
      humidity: number;
    };
    weather: Array<{
      description: string;
    }>;
    wind: {
      speed: number;
    };
  } | null>(null);
  
  const loading = ref(false);
  
  watch(() => props.weather.coordinates[0], async (newLoc) => {
    if (!newLoc) return;
  
    loading.value = true;
    weather.value = await getCurrentForecast(newLoc);
    loading.value = false;
  }, { immediate: true });
  </script>

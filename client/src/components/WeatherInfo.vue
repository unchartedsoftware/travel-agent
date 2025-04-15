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
  // import type { WeatherStop } from '../models/types';
  import { getCurrentForecast, getFutureForecastAtTime } from '../utilities/weather';
  
  const props = defineProps<{
    weather: any;
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
  const unchartedOffice: [number, number] = [43.65035550554264, -79.36450868771557];
  
  watch(() => props.weather, async (newLoc) => {
    if (!newLoc) return;
  
    loading.value = true;
    weather.value = await getCurrentForecast(unchartedOffice);
    console.log(await getFutureForecastAtTime(unchartedOffice, '2025-04-15T18:47:16+0000'))
    loading.value = false;
  }, { immediate: true });
  </script>

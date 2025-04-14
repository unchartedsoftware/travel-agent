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
  
  <script setup>
  import { ref, watch } from 'vue';
  import axios from 'axios';
  
  const props = defineProps({
    location: Object,
    apikey: String
  });
  
  const weather = ref(null);
  const loading = ref(false);
  const apiKey = '11fcb59c7eec3a76e6b54c1b93b590a7';
  
  watch(() => props.location, async (newLoc) => {
    if (!newLoc) return;
  
    loading.value = true;
    try {
      const url = `https://api.openweathermap.org/data/2.5/weather?lat=${newLoc[0]}&lon=${newLoc[1]}&units=metric&appid=${apiKey}`;
      const response = await axios.get(url);
      weather.value = response.data;
    } catch (error) {
      console.error("Error fetching weather data:", error);
    } finally {
      loading.value = false;
    }
  }, { immediate: true });
  </script>
  
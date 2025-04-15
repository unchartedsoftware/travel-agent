<script lang="ts">
export default {
  name: 'MapComponent'
}
</script>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { openweathermapApiKey } from '../utilities/weather';

const props = defineProps<{
  route: Array<[number, number]> | null;
  weatherData: Array<{
    position: [number, number];
    forecast: string;
    temperature: number;
  }> | null;
}>();

const mapContainer = ref<HTMLElement | null>(null);
let map: L.Map | null = null;
let routeLine: L.Polyline | null = null;
let weatherMarkers: L.Marker[] = [];

onMounted(() => {
  if (mapContainer.value) {
    map = L.map(mapContainer.value).setView([39.8283, -98.5795], 4); // Center on USA
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors'
    }).addTo(map);
	L.tileLayer(`https://tile.openweathermap.org/map/clouds_new/{z}/{x}/{y}.png?appid=${openweathermapApiKey}`, {
		attribution: '&copy; <a href="https://openweathermap.org/">OpenWeatherMap</a>',
		opacity: 0.8
	}).addTo(map);
	// L.tileLayer(`https://tile.openweathermap.org/map/temp_new/{z}/{x}/{y}.png?appid=${openweathermapApiKey}`, {
	// 	attribution: '&copy; <a href="https://openweathermap.org/">OpenWeatherMap</a>',
	// 	opacity: 0.6
	// }).addTo(map);
	// L.tileLayer(`https://tile.openweathermap.org/map/wind_new/{z}/{x}/{y}.png?appid=${openweathermapApiKey}`, {
	// 	attribution: '&copy; <a href="https://openweathermap.org/">OpenWeatherMap</a>',
	// 	opacity: 0.6
	// }).addTo(map);
	L.tileLayer(`https://tile.openweathermap.org/map/snow/{z}/{x}/{y}.png?appid=${openweathermapApiKey}`, {
		attribution: '&copy; <a href="https://openweathermap.org/">OpenWeatherMap</a>',
		opacity: 0.9
	}).addTo(map);
	L.tileLayer(`https://tile.openweathermap.org/map/rain_new/{z}/{x}/{y}.png?appid=${openweathermapApiKey}`, {
		attribution: '&copy; <a href="https://openweathermap.org/">OpenWeatherMap</a>',
		opacity: 0.9
	}).addTo(map);
  }
});

onUnmounted(() => {
  if (map) {
    map.remove();
  }
});

watch(() => props.route, (newRoute) => {
  if (map && newRoute) {
    if (routeLine) {
      routeLine.remove();
    }
    routeLine = L.polyline(newRoute, { color: 'blue' }).addTo(map);
    map.fitBounds(routeLine.getBounds());
  }
});

watch(() => props.weatherData, (newWeatherData) => {
  if (map && newWeatherData) {
    // Clear existing weather markers
    weatherMarkers.forEach(marker => marker.remove());
    weatherMarkers = [];

    // Add new weather markers
    newWeatherData.forEach(data => {
      const marker = L.marker(data.position)
        .bindPopup(`
          <b>Weather:</b> ${data.forecast}<br>
          <b>Temperature:</b> ${data.temperature}°F
        `)
        .addTo(map);
      weatherMarkers.push(marker);
    });
  }
});
</script>

<template>
  <div ref="mapContainer" style="height: 600px; width: 100%;" />
</template>

<style>
.leaflet-popup-content {
  font-size: 14px;
  line-height: 1.4;
}
</style>
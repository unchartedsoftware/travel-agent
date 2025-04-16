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
    location: string;
    arrivalTime: string;
  }> | null;
}>();

const mapContainer = ref<HTMLElement | null>(null);
let map: L.Map;
let routeLine: L.Polyline | null = null;
let weatherMarkers: L.Marker[] = [];

// Function to determine weather icon based on forecast
const getWeatherIcon = (forecast: string): string => {
  const lowerForecast = forecast.toLowerCase();
  if (lowerForecast.includes('snow') || lowerForecast.includes('sleet')) {
    return 'fa-snowflake';
  } else if (lowerForecast.includes('rain') || lowerForecast.includes('shower')) {
    return 'fa-cloud-rain';
  } else if (lowerForecast.includes('cloud')) {
    return lowerForecast.includes('part') ? 'fa-cloud-sun' : 'fa-cloud';
  } else if (lowerForecast.includes('clear') || lowerForecast.includes('sunny')) {
    return 'fa-sun';
  } else if (lowerForecast.includes('storm') || lowerForecast.includes('thunder')) {
    return 'fa-cloud-bolt';
  } else if (lowerForecast.includes('wind')) {
    return 'fa-wind';
  } else if (lowerForecast.includes('fog') || lowerForecast.includes('mist')) {
    return 'fa-smog';
  }
  return 'fa-cloud'; // default icon
};

// Function to get color class based on temperature
const getTemperatureColorClass = (temp: number): string => {
  if (temp <= 5) return 'weather-icon-cold';
  if (temp >= 20) return 'weather-icon-hot';
  return 'weather-icon-moderate';
};

// Create custom icon for weather markers
const createWeatherIcon = (
  forecast: string,
  temperature: number,
  location: string,
  arrivalTime: string
): L.DivIcon => {
  const iconName = getWeatherIcon(forecast);
  const colorClass = getTemperatureColorClass(temperature);
  const date = new Date(arrivalTime);
  const formattedDate = date.toLocaleString('en-US', {
    hour: '2-digit',
    minute: '2-digit'
  });

  return L.divIcon({
    html: `<div class="weather-marker ${colorClass}">
            <div class="time">${formattedDate}</div>
            <i class="fas ${iconName}" />
            <div class="temp">${temperature}°C</div>
          </div>`,
    className: 'weather-marker-container',
    iconSize: [70, 70],
    iconAnchor: [35, 35]
  });
};

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
    if (newRoute && newRoute.length > 0) {
      map.setView(newRoute[0], 10); // Center the map on the first point of the new route
      routeLine = L.polyline(newRoute, { color: 'blue' }).addTo(map);
      map.fitBounds(routeLine.getBounds());
    }
  }
});

watch(() => props.weatherData, (newWeatherData) => {
  if (map && newWeatherData) {
    // Clear existing weather markers
    weatherMarkers.forEach(marker => marker.remove());
    weatherMarkers = [];

    // Add new weather markers
    newWeatherData.forEach(data => {
      if (map) { // Add null check
        
        const marker = L.marker(data.position, {
          icon: createWeatherIcon(data.forecast, data.temperature, data.location, data.arrivalTime),
        })
          .bindPopup(`
            <div class="weather-popup">
              <p>{data.location}</p>
            </div>
          `)
          // .bindTooltip(`${data.forecast}, ${data.temperature}°C`, {
          //   permanent: true, // Keeps the tooltip always visible
          //   direction: 'top', // Positions the tooltip above the marker
          //   className: 'weather-tooltip' // Custom class for styling
          // })
          .addTo(map);
        weatherMarkers.push(marker);
      }
    });
  }
});
</script>

<template>
  <div ref="mapContainer" style="height: 600px; width: 100%;" />
</template>

<style>
.weather-marker-container {
  display: flex;
  justify-content: center;
  align-items: center;
  background: none;
  border: none;
  transform: translate(-50%, -50%);  /* Added to help with centering */
}

.weather-marker {
  /* display: flex;
  justify-content: center;
  align-items: center; */
  width: 70px;
  height: 70px;
  background-color: white;
  border-radius: 50%;
  box-shadow: 0 2px 4px rgba(0,0,0,0.2);

  i {
    width: 33px;
    height: 33px;
    font-size: medium;
  }



  .temp, .time {
    margin-top: 7px;
  }
}

.weather-popup {
  font-size: 14px;
  line-height: 1.4;
}

.weather-icon-cold { background-color: #85b4ff; }   /* Blue */
.weather-icon-moderate { background-color: #eee; }  /* Gray */
.weather-icon-hot { background-color: #f19f9f; }    /* Red */
.text-2xl { font-size: 1.5rem; }
</style>

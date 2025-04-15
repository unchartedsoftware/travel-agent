
import axios from 'axios';
// import type { WeatherStop } from '../models/types'

// const tomorrowUrl = 'https://api.tomorrow.io/v4/weather/forecast?location=42.3478,-71.0466&apikey=';
const owmUrl = 'https://api.openweathermap.org/data/2.5/';

export const openweathermapApiKey = '11fcb59c7eec3a76e6b54c1b93b590a7';
export const tomorrowApiKey = 'iXVkLLrGwlwtH2vT3aU1gYsr8YmKRfHo';
const ONE_HOUR = 3600;
const THREE_HOURS = 10800;

export async function getCurrentForecast(location: [number, number]) {
  const weather = await weatherFetch(`https://api.openweathermap.org/data/2.5/weather?lat=${location[0]}&lon=${location[1]}&units=metric&appid=${openweathermapApiKey}`);
  return weather
}

export async function getFutureForecastAtTime(location: [number, number], datetime: string) {
  const time = isoStringToTimestamp(datetime);
  const forecast = await weatherFetch(`${owmUrl}forecast?lat=${location[0]}&lon=${location[1]}&units=metric&appid=${openweathermapApiKey}`);
  console.log(forecast);
  return forecast.list.find((li) => li.dt >= time && li.dt <= time + THREE_HOURS);
}

async function weatherFetch(url: string) {
    try {
        const response = await axios.get(url);
        return response.data;
      } catch (error) {
        console.error("Error fetching weather data:", error);
      } 
}

function isoStringToTimestamp(datetime: string) {
  const date = new Date(datetime);
  return Math.floor(date.getTime() / 1000);
}
export interface WeatherStop {
  location: string;
  arrival_time: string;
  weather: string;
}

export interface RouteOption {
  id: number;
  departureTime: string;
  estimatedDuration: string;
  weatherRisk: 'Low' | 'Medium' | 'High';
  stops: WeatherStop[];
  score: number;
  coordinates: [number, number][];
}

export interface TripFormData {
  start: string;
  end: string;
  departureDate: string;
}

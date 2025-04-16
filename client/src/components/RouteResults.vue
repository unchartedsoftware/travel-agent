<script lang="ts">
export default {
  name: 'RouteResults'
}
</script>

<script setup lang="ts">
import Card from 'primevue/card';
import Timeline from 'primevue/timeline';
import Accordion from 'primevue/accordion';
import AccordionTab from 'primevue/accordiontab';
import Tag from 'primevue/tag';
import type { RouteOption } from '../models/types';

defineProps<{
  routes: RouteOption[];
}>();

const getScoreSeverity = (score: number) => {
  if (score >= 80) return 'success';
  if (score >= 60) return 'warning';
  return 'danger';
};

const getWeatherRiskSeverity = (risk: string) => {
  switch (risk) {
    case 'Low': return 'success';
    case 'Medium': return 'warning';
    case 'High': return 'danger';
    default: return 'info';
  }
};
</script>

<template>
  <Card class="w-full">
    <template #title>Recommended Routes</template>
    <template #content>
      <Accordion class="w-full">
        <AccordionTab v-for="route in routes" :key="route.id">
          <template #header>
            <div class="flex align-items-center justify-content-between w-full">
              <div class="flex flex-column md:flex-row gap-3 align-items-start md:align-items-center flex-1">
                <span class="whitespace-nowrap">Departure: {{ route.departure_time }}</span>
                <span class="whitespace-nowrap">Duration: {{ (route.estimated_duration/6000).toFixed(2) }} hours</span>
                <Tag :severity="getScoreSeverity(route.score)" class="ml-auto">
                  Score: {{ route.score }}
                </Tag>
              </div>
            </div>
          </template>

          <Timeline :value="route.stops" class="w-full mt-3">
            <template #content="slotProps">
              <div class="timeline-item w-full">
                <h5>{{ slotProps.item.location }}</h5>
                <p>Arrival: {{ slotProps.item.arrivalTime }}</p>
                <p>{{ slotProps.item.weather }}</p>
              </div>
            </template>
          </Timeline>

          <div class="mt-3">
            <Tag :severity="getWeatherRiskSeverity(route.weatherRisk)">
              Weather Risk: {{ route.weatherRisk }}
            </Tag>
          </div>
        </AccordionTab>
      </Accordion>
      {{  route }}
    </template>
  </Card>
</template>

<style scoped>
.timeline-item {
  padding: 0.5rem;
  width: 100%;
}
.timeline-item h5 {
  margin: 0 0 0.5rem 0;
  font-size: 0.88rem;
}
.timeline-item p {
  margin: 0.25rem 0;
}
.flex {
  display: flex;
}
.flex-1 {
  flex: 1;
}
.flex-column {
  flex-direction: column;
}
.align-items-center {
  align-items: center;
}
.align-items-start {
  align-items: flex-start;
}
.justify-content-between {
  justify-content: space-between;
}
.w-full {
  width: 100%;
}
.gap-3 {
  gap: 1rem;
}
.mt-3 {
  margin-top: 1rem;
}
.ml-auto {
  margin-left: auto;
}
.whitespace-nowrap {
  white-space: nowrap;
}

:deep(.p-accordion-content) {
  overflow-x: hidden;
}

@media (max-width: 768px) {
  .timeline-item h5 {
    font-size: 0.8rem;
  }
}
</style>

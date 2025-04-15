<script lang="ts">
export default {
  name: 'TripPlanningForm'
}
</script>

<script setup lang="ts">
import { ref } from 'vue';
import Card from 'primevue/card';
import InputText from 'primevue/inputtext';
import Calendar from 'primevue/calendar';

import Button from 'primevue/button';
import type { TripFormData } from '../models/types';

const startLocation = ref('');
const endLocation = ref('');
const earliestDepartureDate = ref<Date | null>(null);

const emit = defineEmits<{
  (e: 'planTrip', data: TripFormData): void
}>();

const submitForm = () => {
  if (!earliestDepartureDate.value) return;

  emit('planTrip', {
    start: startLocation.value,
    end: endLocation.value,
    departure_time: earliestDepartureDate.value.toISOString()
  });
};
</script>

<template>
  <Card class="w-full">
    <template #title>Plan Your Trip</template>
    <template #content>
      <form @submit.prevent="submitForm" class="flex flex-column gap-3">
        <div class="field w-full">
          <span class="p-float-label w-full">
            <InputText
              id="startLocation"
              v-model="startLocation"
              class="w-full"
            />
            <label for="startLocation">Starting Location</label>
          </span>
        </div>

        <div class="field w-full">
          <span class="p-float-label w-full">
            <InputText
              id="endLocation"
              v-model="endLocation"
              class="w-full"
            />
            <label for="endLocation">Destination</label>
          </span>
        </div>

        <div class="field w-full">
          <span class="p-float-label w-full">
            <Calendar
              :showTime="true"
              :hourFormat="24"
              id="departureDate"
              v-model="earliestDepartureDate"
              dateFormat="yy-mm-dd hh:mm"
              class="w-full"
              showIcon
            />
            <label for="departureDate">Earliest Departure Date</label>
          </span>
        </div>

        <Button
          type="submit"
          label="Plan Route"
          icon="pi pi-search"
          class="w-full"
          :disabled="!startLocation || !endLocation || !earliestDepartureDate"
        />
      </form>
    </template>
  </Card>
</template>

<style scoped>
button {
  color: black;
}
.field {
  margin-bottom: 1.5rem;
  width: 100%;
}
.w-full {
  width: 100%;
  stroke:black;
  color: black
}
.flex {
  display: flex;
}
.flex-column {
  flex-direction: column;
}
.gap-3 {
  gap: 1rem;
}
:deep(.p-calendar) {
  width: 100%;
}
:deep(.p-inputtext) {
  width: 100%;
}
:deep(.p-button) {
  width: 100%;
}
</style>

<template>
  <Card class="w-full">
    <template #title>AI Travel Agent Suggestions</template>
    <template #content>
      <Accordion class="w-full">
        <AccordionTab header="Travel Agent Recommendations">
          <div v-for="(message, index) in formattedMessages" :key="index" class="message-item markdown-content" v-html="message">
          </div>
        </AccordionTab>
      </Accordion>
    </template>
  </Card>
</template>

<script lang="ts">
export default {
  name: 'AIMessages'
}
</script>

<script setup lang="ts">
import { computed } from 'vue';
import Card from 'primevue/card';
import Accordion from 'primevue/accordion';
import AccordionTab from 'primevue/accordiontab';
import { marked } from 'marked';

const props = defineProps<{
  messages: string[];
}>();

const formattedMessages = computed(() => 
  props.messages.map(message => marked(message))
);
</script>

<style scoped>
.message-item {
  padding: 0.5rem 0;
  border-bottom: 1px solid var(--surface-border);
  text-align: left;
}
.message-item:last-child {
  border-bottom: none;
}
.w-full {
  width: 100%;
}
:deep(.markdown-content) {
  /* Add styling for markdown elements */
  & h1, & h2, & h3, & h4, & h5, & h6 {
    margin-top: 1em;
    margin-bottom: 0.5em;
  }
  & p {
    margin-bottom: 1em;
  }
  & ul, & ol {
    margin-bottom: 1em;
    padding-left: 2em;
  }
  & code {
    background-color: var(--surface-200);
    padding: 0.2em 0.4em;
    border-radius: 3px;
    font-family: monospace;
  }
  & pre {
    background-color: var(--surface-200);
    padding: 1em;
    border-radius: 4px;
    overflow-x: auto;
  }
  & blockquote {
    border-left: 4px solid var(--primary-color);
    margin-left: 0;
    padding-left: 1em;
    color: var(--text-color-secondary);
  }
  & table {
    border-collapse: collapse;
    width: 100%;
    margin-bottom: 1em;
  }
  & th, & td {
    border: 1px solid var(--surface-border);
    padding: 0.5em;
  }
  & a {
    color: var(--primary-color);
    text-decoration: none;
    &:hover {
      text-decoration: underline;
    }
  }
}
</style>
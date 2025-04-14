/// <reference types="vite/client" />

declare module 'primevue/config' {
  import { Plugin } from 'vue'
  const plugin: Plugin
  export default plugin
}

declare module 'primevue/*' {
  import { Component } from 'vue'
  const component: Component
  export default component
}

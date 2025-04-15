import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import PrimeVue from 'primevue/config'
import ProgressSpinner from 'primevue/progressspinner'
import Accordion from 'primevue/accordion'
import AccordionTab from 'primevue/accordiontab'

// Import Font Awesome
import '@fortawesome/fontawesome-free/css/all.css'

// Import PrimeVue styles
import 'primevue/resources/themes/saga-blue/theme.css'
import 'primevue/resources/primevue.min.css'
import 'primeicons/primeicons.css'
import 'primeflex/primeflex.css'

const app = createApp(App)
app.use(PrimeVue)
app.component('ProgressSpinner', ProgressSpinner)
app.component('Accordion', Accordion)
app.component('AccordionTab', AccordionTab)
app.mount('#app')

import './main.css'
import { createApp } from 'vue'
import App from './App.vue'

// Register chartjs-plugin-zoom + the date-fns time adapter once on the
// global Chart registry so that every Chart.js instance created by the
// app picks them up automatically.
import { Chart } from 'chart.js'
import zoomPlugin from 'chartjs-plugin-zoom'
import 'chartjs-adapter-date-fns'
Chart.register(zoomPlugin)

createApp(App).mount('#app')

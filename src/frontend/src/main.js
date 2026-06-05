import './main.css'
import { createApp } from 'vue'
import App from './App.vue'

// uPlot is imported per-component (TrendChart.vue) since it does not need
// any global plugin registration — its CSS is pulled in there as well.

createApp(App).mount('#app')

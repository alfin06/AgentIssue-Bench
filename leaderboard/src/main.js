import './assets/main.css'

import { createApp } from 'vue'
import App from './App.vue'
import router from './router' // ⬅️ Import the router
import 'bootstrap/dist/css/bootstrap.min.css'

createApp(App).use(router).mount('#app')

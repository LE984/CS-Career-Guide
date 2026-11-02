import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './style.css'
import './assets/css/morph-btn.css'
import './assets/css/career-theme.css'
import './assets/css/minimal-theme.css'

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.mount('#app')

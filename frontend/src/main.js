import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

// Vuetify
import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

// Element Plus
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

// Global styles
import './styles/global.css'

// Create Vuetify instance with a minimalist theme
const vuetify = createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: 'dark',
    themes: {
      dark: {
        dark: true,
        colors: {
          background: '#000000',
          surface: '#000000',
          primary: '#ffffff',
          secondary: '#ffffff',
        }
      }
    }
  }
})

// Create and mount the Vue application
createApp(App)
  .use(router)
  .use(vuetify)
  .use(ElementPlus)
  .mount('#app') 
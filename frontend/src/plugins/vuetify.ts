import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import '@mdi/font/css/materialdesignicons.css'

export const vuetify = createVuetify({
  theme: {
    defaultTheme: 'light',
    themes: {
      light: {
        colors: {
          kakao: '#FEE500',
          background: '#f6f7fb',
          surface: '#ffffff',
          primary: '#7C4DFF',
        },
      },
      dark: {
        colors: {
          kakao: '#FEE500',
          background: '#0f172a',
          surface: '#111827',
          primary: '#8b5cf6',
        },
      },
    },
  },
  icons: {
    defaultSet: 'mdi',
  },
})

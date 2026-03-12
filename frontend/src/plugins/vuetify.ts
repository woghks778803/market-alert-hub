import "vuetify/styles"
import { createVuetify } from "vuetify"
import "@mdi/font/css/materialdesignicons.css"
export const vuetify = createVuetify({
    theme: {
        defaultTheme: 'light',
        themes: {
            light: {
                colors: {
                    kakao: '#FEE500',
                },
            },

        },
    },
    icons: {
        defaultSet: "mdi"
    }
})

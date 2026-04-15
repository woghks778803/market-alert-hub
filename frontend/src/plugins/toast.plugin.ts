import 'vue3-toastify/dist/index.css'
import { updateGlobalOptions } from "vue3-toastify"

export function createToastPlugin() {
    updateGlobalOptions({
        limit: 3,
        autoClose: 3000,
        closeOnClick: true,
        pauseOnHover: true,
        hideProgressBar: false,
        newestOnTop: true,
    })

    return {
        install() {
            // plugin wrapper
        },
    }
}
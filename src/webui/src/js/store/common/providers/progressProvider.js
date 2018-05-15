import { Provider } from 'cerebral'
import NProgress from 'nprogress'

NProgress.configure({
    minimum: 0.5,
    showSpinner: false,
    trickleSpeed: 100
})

export default Provider({
    start() {
        NProgress.start()
    },
    inc() {
        NProgress.inc()
    },
    set(opt) {
        NProgress.set(opt)
    },
    done(opt) {
        NProgress.done(opt)
    }
})

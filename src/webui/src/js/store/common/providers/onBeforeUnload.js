import { Provider } from 'cerebral'

export default Provider({
    enable(checkFunc, message) {
        const state = this.context.controller.getModel().state
        window.onbeforeunload = (event) => {
            if (checkFunc(state)) {
                event.returnValue = message
            }
        }
    },
    disable() {
        window.onbeforeunload = null
    }
})

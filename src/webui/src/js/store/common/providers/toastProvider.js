import { Provider } from 'cerebral'
import toastr from 'toastr'

export default Provider({
    show(type, message, timeout = 3000, closeButton = false) {
        const options = {
            timeOut: timeout,
            tapToDismiss: false
        }
        if (closeButton) {
            options.timeOut = 0
            options.extendedTimeOut = 0
            options.closeButton = true
            options.closeHtml = '<button>CLOSE</button>'
        }
        toastr[type](message, null, options)
    }
})

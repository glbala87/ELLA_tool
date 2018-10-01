import { Provider } from 'cerebral'
import toastr from 'toastr'

export default Provider({
    show(type, message, timeout = 1000) {
        toastr[type](message, null, { timeOut: timeout })
    }
})

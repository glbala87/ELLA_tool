import { Provider } from 'cerebral'
import toastr from 'toastr'

export default Provider({
    show(type, message, timeout = 3000) {
        toastr[type](message, null, { timeOut: timeout })
    }
})

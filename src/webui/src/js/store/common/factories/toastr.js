function toastr(type, title, timeout = 1000) {
    return function _toastr({ toastr, resolve }) {
        toastr[type](resolve.value(title), null, { timeOut: timeout })
    }
}

export default toastr

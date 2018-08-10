export default function toast(type, title, timeout) {
    return function toast({ toast, resolve }) {
        toast.show(type, resolve.value(title), timeout)
    }
}

export default function toast(type, title, timeout) {
    return function toast({ toast, resolve, props, state, execution }) {
        if (
            execution.__ignoreError ||
            ('error' in props &&
                props.error.message === 'request abort' &&
                props.error.name === 'HttpProviderError')
        ) {
            console.error(`Suppresing toast: ${type} - ${resolve.value(title)}`)
            return
        }
        toast.show(type, resolve.value(title), timeout)
    }
}

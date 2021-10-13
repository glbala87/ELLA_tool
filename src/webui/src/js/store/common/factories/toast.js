export default function toast(type, title, timeout) {
    return ({ toast, resolve, props, state, execution }) => {
        if (
            execution.__ignoreError ||
            (props.error &&
                props.error.message === 'request abort' &&
                props.error.name === 'HttpProviderError')
        ) {
            console.error(`Suppresing toast: ${type} - ${resolve.value(title)}`)
            return
        }
        toast.show(type, resolve.value(title), timeout)
    }
}

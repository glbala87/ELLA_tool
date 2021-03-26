export default function postException({ route, http, props, state, execution }) {
    const { error } = props
    // Do not post errors if errors are set to be ignored, or if they are caused by explicit abortion
    // of http requests
    const payload = {
        message: `${error.name}: ${error.message}`,
        location: route.current(),
        stacktrace: error.stack,
        state: state.get()
    }
    if (
        execution.__ignoreError ||
        (error.name === 'HttpProviderError' && error.message === 'request abort')
    ) {
        console.error(`Not posting exception: ${payload.message}`)
        return
    } else {
        console.error(`Posting exception: ${payload.message}`)
        http.post('ui/exceptionlog/', payload)
    }
}

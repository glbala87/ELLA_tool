export default function postException({ route, http, props, state }) {
    const { error } = props

    error.resource = console.log(error.resource)

    const payload = {
        message: `${error.name}: ${error.message}`,
        location: route.current(),
        stacktrace: error.stack,
        state: state.get()
    }
    http.post('ui/exceptionlog/', payload)
}

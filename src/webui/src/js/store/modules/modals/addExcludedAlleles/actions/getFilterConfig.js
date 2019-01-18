export default function({ http, state, props, path }) {
    // Get filter config from loaded filter configs if already loaded as part of available filter configs.
    // Otherwise, get filter config from backend
    const filterconfigId = state.get(`views.workflows.interpretation.state.filterconfigId`)
    const loadedFilterconfigs = state.get(`views.workflows.data.filterconfigs`)

    let filterconfig = loadedFilterconfigs.find((fc) => fc.id == filterconfigId)
    if (filterconfig) {
        return path.success({ result: filterconfig })
    } else {
        return http
            .get(`filterconfigs/${filterconfigId}`)
            .then((response) => {
                return path.success({ result: response.result })
            })
            .catch((response) => {
                return path.error({ result: response.result })
            })
    }
}

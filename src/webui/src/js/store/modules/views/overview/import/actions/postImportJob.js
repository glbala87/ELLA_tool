export default function postImportJob({ state, props, http, path }) {
    const selectedSample = state.get('views.overview.import.selectedSample')
    const { name, version } = props.genepanel
    const payload = {
        sample_id: selectedSample.name,
        genepanel_name: name,
        genepanel_version: version
    }
    return http
        .post('import/service/jobs/', payload)
        .then((response) => {
            return path.success({ result: response.result })
        })
        .catch((error) => {
            console.error(error)
            return path.error(error)
        })
}

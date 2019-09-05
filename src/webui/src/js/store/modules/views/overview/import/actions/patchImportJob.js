export default function patchImportJob({ http, path, props }) {
    const { payload, jobId } = props
    return http
        .patch(`import/service/jobs/${jobId}`, payload)
        .then((response) => {
            return path.success({ result: response.result })
        })
        .catch((response) => {
            console.error(response)
            return path.error(response)
        })
}

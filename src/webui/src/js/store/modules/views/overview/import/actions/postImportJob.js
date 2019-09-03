export default function postImportJob({ props, http, path }) {
    const { importJob, importJobs } = props

    const toImport = importJobs || []
    if (importJob) {
        toImport.push(importJob)
    }
    const promises = []
    for (const payload of toImport) {
        promises.push(http.post('import/service/jobs/', payload))
    }
    return Promise.all(promises)
        .then((responses) => {
            return path.success()
        })
        .catch((error) => {
            console.error(error)
            return path.error(error)
        })
}

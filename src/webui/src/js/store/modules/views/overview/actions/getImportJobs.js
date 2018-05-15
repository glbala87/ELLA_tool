export default function getImportJobs({ http, path, props }) {
    const q = props.q || null
    const page = props.page || null
    const perPage = props.perPage || null

    const query = {
        q: JSON.stringify(q),
        page,
        per_page: perPage
    }

    return http
        .get(`import/service/jobs/`, query)
        .then((response) => {
            const result = {
                entries: response.result,
                pagination: {
                    page: response.headers['page'],
                    totalCount: response.headers['total-count'],
                    perPage: response.headers['per-page'],
                    totalPages: response.headers['total-pages']
                }
            }
            return path.success({ result })
        })
        .catch((response) => {
            return path.error(response)
        })
}

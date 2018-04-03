export default function getImportJobs({ http, path, props }) {
    const q = props.q || null
    const page = props.page || null
    const perPage = props.perPage || null

    // TODO: Create more generic pagination provider
    const args = []
    if (q) {
        args.push(`q=${encodeURIComponent(JSON.stringify(q))}`)
    }
    if (perPage) {
        args.push(`per_page=${perPage}`)
    }
    if (page) {
        args.push(`page=${page}`)
    }
    let extras = ''
    if (!args.length) {
        extras = `?${args.join('&')}`
    }
    return http
        .get(`import/service/jobs/${extras}`)
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

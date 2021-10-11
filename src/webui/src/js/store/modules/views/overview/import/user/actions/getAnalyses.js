export default ({ props, http, state, path }) => {
    const { search, perPage } = props

    let query = `q=${encodeURIComponent(JSON.stringify({ name: { $ilike: `%${search}%` } }))}`
    if (perPage !== undefined && perPage !== null) {
        query += `&per_page=${perPage}`
    }

    return http
        .get(`analyses/?${query}`)
        .then((response) => {
            return path.success({ result: response.result })
            state.set(
                `views.overview.import.user.jobData.${index}.analysesOptions`,
                response.result
            )
        })
        .catch((error) => {
            return path.error(error)
        })
}

import processAnalyses from '../../../../common/helpers/processAnalyses'

export default function getOverviewAnalysesFinalized({ http, path, props }) {
    const { page: selectedPage } = props

    return http
        .get(`overviews/analyses/finalized/?per_page=10&page=${selectedPage}`)
        .then((response) => {
            processAnalyses(response.result)

            let result = {
                entries: response.result,
                pagination: {
                    page: parseInt(response.headers['page']),
                    totalCount: parseInt(response.headers['total-count']),
                    perPage: parseInt(response.headers['per-page']),
                    totalPages: parseInt(response.headers['total-pages'])
                }
            }

            return path.success({ result })
        })
        .catch((response) => {
            return path.error(response)
        })
}

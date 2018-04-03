import processAnalyses from '../../../../common/helpers/processAnalyses'

export default function getOverviewAnalysesFinalized({ module, http, path, props }) {
    let sections = module.get('sections')
    let selectedPage = sections[props.section].finalized.selectedPage

    return http
        .get(`overviews/analyses/finalized/?per_page=10&page=${selectedPage}`)
        .then((response) => {
            processAnalyses(response.result)

            let result = {
                entries: response.result,
                pagination: {
                    // TODO: Refactor this to provider!
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

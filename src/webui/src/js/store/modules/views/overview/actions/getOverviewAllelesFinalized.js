import processAlleles from '../../../../common/helpers/processAlleles'

function getOverviewAllelesFinalized({ module, http, path, props }) {
    let sections = module.get('sections')
    let selectedPage = sections[props.section].finalized.selectedPage

    return http
        .get(`overviews/alleles/finalized/?per_page=10&page=${selectedPage}`)
        .then((response) => {
            for (let item of response.result) {
                processAlleles([item.allele], item.genepanel)
            }
            let result = {
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

export default getOverviewAllelesFinalized

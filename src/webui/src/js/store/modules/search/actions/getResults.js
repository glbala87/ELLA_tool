import processAlleles from '../../../common/helpers/processAlleles'
import processAnalyses from '../../../common/helpers/processAnalyses'

function getResults({ http, module, path, state }) {
    let query = module.get('query')
    let page = module.get('page')
    let per_page = module.get('per_page')
    let limit = module.get('limit')

    return http
        .get(
            `search/?q=${encodeURIComponent(
                JSON.stringify(query)
            )}&page=${page}&per_page=${per_page}&limit=${limit}`
        )
        .then((response) => {
            for (let item of response.result.alleles) {
                processAlleles([item.allele])
            }
            processAnalyses(response.result.analyses)

            return path.success({
                result: response.result,
                totalCount: Number(response.headers['total-count'])
            })
        })
        .catch((response) => {
            console.log(response)
            return path.error({ result: response.result })
        })
}

export default getResults

import processAlleles from '../../../common/helpers/processAlleles'
import processAnalyses from '../../../common/helpers/processAnalyses'

function getResults({ http, module, path, state }) {
    const config = state.get('app.config')
    let query = module.get('query')
    return http
        .get(`search?q=${encodeURIComponent(JSON.stringify(query))}`)
        .then((response) => {
            for (let item of response.result.alleles) {
                processAlleles([item.allele], config)
            }
            processAnalyses(response.result.analyses)

            return path.success({ result: response.result })
        })
        .catch((response) => {
            console.log(response)
            return path.error({ result: response.result })
        })
}

export default getResults

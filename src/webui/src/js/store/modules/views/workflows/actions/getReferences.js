import processReferences from '../../../../common/helpers/processReferences'

function getReferences({ http, path, state }) {
    let alleles = state.get('views.workflows.interpretation.data.alleles')
    // Get all reference ids from alleles
    let ids = []
    let pubmedIds = []
    for (let allele of Object.values(alleles)) {
        for (let ref of allele.annotation.references) {
            if (ref.id) {
                ids.push(ref.id)
            } else if (ref.pubmed_id) {
                pubmedIds.push(ref.pubmed_id)
            }
        }
    }
    ids = [...new Set(ids)]
    pubmedIds = [...new Set(pubmedIds)]

    let refById = http.get(`references/`, { q: JSON.stringify({ id: ids }) })
    let refByPmid = http.get(`references/`, { q: JSON.stringify({ pubmed_id: pubmedIds }) })
    let references = []
    return Promise.all([refById, refByPmid])
        .then((args) => {
            let [refId, refByPmid] = args
            references = refId.result.concat(refByPmid.result)
        })
        .then((response) => {
            processReferences(references)
            let result = {}
            for (let r of references) {
                result[r.id] = r
            }
            return path.success({ result: result })
        })
        .catch((response) => {
            return path.error({ result: response.result })
        })
}

export default getReferences

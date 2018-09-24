import processAlleles from '../../../../common/helpers/processAlleles'

export default function({ http, path, module }) {
    // TODO: Support partial loading of alleles to support large samples
    const analysis = module.get('data.analysis')
    const interpretation = module.get('interpretation.selected')

    const alleleIds = []
    for (let ids of Object.values(interpretation.excluded_allele_ids)) {
        alleleIds.push(...ids)
    }

    const q = JSON.stringify({
        id: alleleIds
    })

    return http
        .get(`alleles/`, {
            q,
            gp_name: genepanel.name,
            gp_version: genepanel.version,
            sample_id: analysis.samples[0].id // TODO: Support multiple samples
        })
        .then((response) => {
            let alleles = response.result
            processAlleles(alleles, null)

            // Structure as {alleleId: allele}
            let allelesById = {}
            for (let allele of alleles) {
                allelesById[allele.id] = allele
            }

            return path.success({ result: allelesById })
        })
        .catch((response) => {
            return path.error({ result: response.result })
        })
}

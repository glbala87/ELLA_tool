import processAlleles from '../../../../common/helpers/processAlleles'

const TYPES = {
    analysis: 'analyses',
    allele: 'alleles'
}

function getAlleles({ http, path, state }) {
    const type = TYPES[state.get('views.workflows.type')]
    const id = state.get('views.workflows.id')
    const selectedInterpretation = state.get('views.workflows.interpretation.selected')
    const getCurrentData = selectedInterpretation.current || false
    const genepanel = state.get('views.workflows.data.genepanel')
    let alleleIds = state.get('views.workflows.interpretation.selected.allele_ids')

    if ('manuallyAddedAlleles' in selectedInterpretation.state) {
        alleleIds = alleleIds.concat(selectedInterpretation.state.manuallyAddedAlleles)
    }
    if (alleleIds.length) {
        return http
            .get(`workflows/${type}/${id}/interpretations/${selectedInterpretation.id}/alleles/`, {
                allele_ids: alleleIds.join(','),
                current: getCurrentData // Only relevant when interpretation status is 'Done'
            })
            .then(response => {
                let alleles = response.result
                processAlleles(alleles, genepanel)

                // Structure as {alleleId: allele}
                let allelesById = {}
                for (let allele of alleles) {
                    allelesById[allele.id] = allele
                }

                return path.success({ result: allelesById })
            })
            .catch(response => {
                return path.error({ result: response.result })
            })
    } else {
        return path.success({ result: {} })
    }
}

export default getAlleles

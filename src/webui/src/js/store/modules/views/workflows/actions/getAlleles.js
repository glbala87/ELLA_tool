import processAlleles from '../../../../common/helpers/processAlleles'
import getSelectedInterpretation from '../computed/getSelectedInterpretation'
import getAlleleIdsFromInterpretation from '../computed/getAlleleIdsFromInterpretation'

const TYPES = {
    analysis: 'analyses',
    allele: 'alleles'
}

function getAlleles({ http, path, state, resolve }) {
    const config = state.get('app.config')
    const genepanel = state.get('views.workflows.interpretation.data.genepanel')

    // There's two possible scenarios:
    // - No existing interpretations -> use normal allele resource
    //   Can only happen for 'allele' type. If so, we need to use the /allele/ resource to load the allele.
    //   We still get the allele id from the 'fake' interpretation
    // - Existing interpretations -> use workflow's allele resource (it can handle historical data)

    const interpretations = state.get('views.workflows.data.interpretations')
    const hasInterpretations = Boolean(interpretations.length)
    const selectedInterpretation = resolve.value(getSelectedInterpretation)
    const selectedInterpretationId = state.get('views.workflows.interpretation.selectedId')
    const alleleIds = resolve.value(getAlleleIdsFromInterpretation)

    let uri = null
    let params = null
    const type = TYPES[state.get('views.workflows.type')]

    if (hasInterpretations) {
        const id = state.get('views.workflows.id')
        const getCurrentData = selectedInterpretationId === 'current'

        uri = `workflows/${type}/${id}/interpretations/${selectedInterpretation.id}/alleles/`
        params = {
            allele_ids: alleleIds.join(','),
            current: getCurrentData // Only relevant when interpretation status is 'Done'
        }
    } else {
        if (type !== 'alleles') {
            console.error(`Invalid workflow type ${type}`)
            return path.error()
        }
        uri = `alleles/`
        params = {
            q: JSON.stringify({ id: alleleIds }),
            gp_name: genepanel.name,
            gp_version: genepanel.version
        }
    }
    if (alleleIds.length) {
        return http
            .get(uri, params)
            .then((response) => {
                let alleles = response.result
                processAlleles(alleles, config, genepanel)

                // Structure as {alleleId: allele}
                let allelesById = {}
                for (let allele of alleles) {
                    allelesById[allele.id] = allele
                }

                return path.success({ result: allelesById })
            })
            .catch((error) => {
                console.error(error)
                return path.error(error)
            })
    } else {
        return path.success({ result: {} })
    }
}

export default getAlleles

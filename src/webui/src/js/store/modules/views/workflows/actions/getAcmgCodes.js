import getReferenceAssessment from '../interpretation/computed/getReferenceAssessment'
import {
    getReferencesIdsForAllele,
    findReferencesFromIds
} from '../../../../common/helpers/reference'

const TYPES = {
    analysis: 'analyses',
    allele: 'alleles'
}

function getAcmgCodes({ http, path, state, props, resolve }) {
    const alleles = state.get('views.workflows.data.alleles')
    const references = Object.values(state.get('views.workflows.data.references'))
    const genepanelName = state.get('views.workflows.data.genepanel.name')
    const genepanelVersion = state.get('views.workflows.data.genepanel.version')
    const referenceAssessments = []

    // We need to get all referenceassessments, either from state or from allele if reused
    for (let [alleleId, allele] of Object.entries(alleles)) {
        const alleleReferenceIds = getReferencesIdsForAllele(allele)
        const alleleReferences = findReferencesFromIds(references, alleleReferenceIds).references
        for (let reference of alleleReferences) {
            const alleleReferenceAssessment = resolve.value(
                getReferenceAssessment(parseInt(alleleId), reference.id)
            )
            if (alleleReferenceAssessment) {
                referenceAssessments.push(alleleReferenceAssessment)
            }
        }
    }

    if (Object.keys(alleles).length) {
        // This resource is POST even though it's only getting data
        return http
            .post(`acmg/alleles/`, {
                allele_ids: Object.keys(alleles),
                gp_name: genepanelName,
                gp_version: genepanelVersion,
                referenceassessments: referenceAssessments
            })
            .then((response) => {
                return path.success({ result: response.result })
            })
            .catch((response) => {
                return path.error({ result: response.result })
            })
    } else {
        return path.success({ result: {} })
    }
}

export default getAcmgCodes

import getAlleleState from '../computed/getAlleleState'
import {
    getReferencesIdsForAllele,
    findReferencesFromIds
} from '../../../../../common/helpers/reference'

export default function autoIgnoreReferences({ state, resolve }) {
    const alleles = state.get('views.workflows.interpretation.data.alleles')
    const refObj = state.get('views.workflows.interpretation.data.references')
    let references = []
    if (refObj) {
        references = Object.values(refObj)
    }
    const userConfig = state.get('app.config.user.user_config')
    if (
        !'interpretation' in userConfig ||
        !'autoIgnoreReferencePubmedIds' in userConfig.interpretation ||
        !userConfig.interpretation.autoIgnoreReferencePubmedIds
    ) {
        return
    }

    for (let [alleleId, allele] of Object.entries(alleles)) {
        const alleleState = resolve.value(getAlleleState(alleleId))
        const alleleReferenceIds = getReferencesIdsForAllele(allele)
        const alleleReferences = findReferencesFromIds(references, alleleReferenceIds).references

        for (let ref of alleleReferences) {
            const refAssesment = alleleState.referenceassessments.find((ra) => {
                return ra.reference_id === ref.id
            })

            if (
                !refAssesment &&
                'pubmed_id' in ref &&
                userConfig.interpretation.autoIgnoreReferencePubmedIds.includes(ref.pubmed_id)
            ) {
                state.push(
                    `views.workflows.interpretation.state.allele.${alleleId}.referenceassessments`,
                    {
                        allele_id: Number(alleleId),
                        reference_id: ref.id,
                        evaluation: {
                            relevance: 'Ignore',
                            comment: 'Automatically ignored according to user group configuration'
                        }
                    }
                )
            }
        }
    }
}

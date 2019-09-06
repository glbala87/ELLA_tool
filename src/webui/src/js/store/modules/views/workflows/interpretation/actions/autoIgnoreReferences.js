import getAlleleState from '../computed/getAlleleState'
import {
    getReferencesIdsForAllele,
    findReferencesFromIds
} from '../../../../../common/helpers/reference'

export default function autoIgnoreReferences({ state, resolve }) {
    const alleles = state.get('views.workflows.interpretation.data.alleles')
    const refObj = state.get('views.workflows.interpretation.data.references')
    // const intData = state.get('views.workflows.interpretation.data')
    // console.log(`intData: ${JSON.stringify(intData, null, 2)}`)
    var references = []
    if (refObj) {
        references = Object.values(refObj)
    }
    const userConfig = state.get('app.config.user.user_config')

    for (let [alleleId, allele] of Object.entries(alleles)) {
        const alleleState = resolve.value(getAlleleState(alleleId))
        console.log(`alleleState: ${JSON.stringify(alleleState, null, 2)}`)
        const alleleReferenceIds = resolve.value(getReferencesIdsForAllele(allele))
        const alleleReferences = resolve.value(
            findReferencesFromIds(references, alleleReferenceIds)
        ).references
        const wat = []
        console.log(`wat (${typeof(wat)}): ${JSON.stringify(wat)}`)
        console.log(`alleleReferences (${typeof(alleleReferences)}): ${JSON.stringify(alleleReferences)}`)

        for (let ref of alleleReferences) {
            const refAssesment = alleleState.referenceassessments.find((ra) => {
                return ra.reference_id === ref.id
            })
            console.log(`checking ref: ${JSON.stringify(ref)}`)
            console.log(`refAssesment: ${JSON.stringify(refAssesment)}`)

            if (
                'pubmed_id' in ref &&
                userConfig.interpretation.filterPubmedReferences.includes(ref.pubmed_id) &&
                !refAssesment
            ) {
                console.log(`pushing new ignore state for ref ${ref.id} with pmid ${ref.pubmed_id}`)
                state.push(
                    `views.workflows.interpretation.state.allele.${alleleId}.referenceassessments`,
                    {
                        allele_id: Number(alleleId),
                        reference_id: ref.id,
                        evaluation: {
                            relevance: 'Ignore',
                            comment: "auto ignored by ELLA"
                        }
                    }
                )
            }
        }
    }
}

import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import setDefaultSelection from '../sequences/setDefaultSelection'
import { deepCopy } from '../../../../../../../util'

const userReferencesForAllele = ({ state, props }) => {
    const { alleleId } = props
    const loadedReferences = state.get(`views.workflows.interpretation.data.references`)
    const userReferenceIds = state
        .get(`views.workflows.interpretation.data.alleles.${alleleId}.annotation.references`)
        .filter((ref) => {
            return ref.source === 'User'
        })
        .map((ref) => {
            const loadedRef = Object.values(loadedReferences).find(
                (r) => (r.pubmed_id && r.pubmed_id === ref.pubmed_id) || (r.id && r.id === ref.id)
            )
            return loadedRef.id
        })
    return { userReferenceIds }
}

export default [
    set(state`views.workflows.modals.addReferences.referenceModes`, ['Search', 'PubMed', 'Manual']),
    set(state`views.workflows.modals.addReferences.referenceMode`, 'Search'),
    setDefaultSelection,
    ({ state }) => {
        state.set(
            `views.workflows.modals.addReferences.data.references`,
            deepCopy(state.get(`views.workflows.interpretation.data.references`))
        )
    },
    userReferencesForAllele,
    set(state`views.workflows.modals.addReferences.userReferenceIds`, props`userReferenceIds`),
    set(state`views.workflows.modals.addReferences.maxSearchResults`, 15),
    set(state`views.workflows.modals.addReferences.alleleId`, props`alleleId`),
    set(state`views.workflows.modals.addReferences.show`, true)
]

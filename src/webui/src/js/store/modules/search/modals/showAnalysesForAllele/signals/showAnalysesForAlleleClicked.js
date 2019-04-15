import { set } from 'cerebral/operators'
import { string, state, props } from 'cerebral/tags'

export default [
    set(state`search.modals.showAnalysesForAllele.allele`, props`allele`),
    set(state`search.modals.showAnalysesForAllele.show`, true)
]

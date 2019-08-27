import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import updateCandidatesFilter from '../sequences/updateCandidatesFilter'

export default [
    set(state`views.overview.import.custom.candidates.filter`, props`filter`),
    updateCandidatesFilter
]

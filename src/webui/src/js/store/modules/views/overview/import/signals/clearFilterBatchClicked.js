import { set } from 'cerebral/operators'
import { state } from 'cerebral/tags'
import updateCandidatesFilter from '../sequences/updateCandidatesFilter'

export default [
    set(state`views.overview.import.custom.candidates.filterBatchOriginal`, ''),
    updateCandidatesFilter
]

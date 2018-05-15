import { toggle } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import showAlleleAssessmentHistoryModal from '../actions/showAlleleAssessmentHistoryModal'

export default [
    showAlleleAssessmentHistoryModal,
    {
        result: [],
        dismissed: []
    }
]

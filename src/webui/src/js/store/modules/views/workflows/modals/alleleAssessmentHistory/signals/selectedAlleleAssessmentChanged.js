import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import updateClassificationDetails from '../sequences/updateClassificationDetails'

export default [
    set(
        state`views.workflows.modals.alleleAssessmentHistory.selectedAlleleAssessment`,
        props`selectedAlleleAssessment`
    ),
    updateClassificationDetails
]

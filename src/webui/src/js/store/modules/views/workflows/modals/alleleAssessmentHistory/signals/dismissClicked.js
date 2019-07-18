import { set } from 'cerebral/operators'
import { state } from 'cerebral/tags'

export default [
    set(state`views.workflows.modals.alleleAssessmentHistory.show`, false),
    set(state`views.workflows.modals.alleleAssessmentHistory.data`, {}),
    set(state`views.workflows.modals.alleleAssessmentHistory.selectedAlleleAssessment`, null),
    set(state`views.workflows.modals.alleleAssessmentHistory.selectedViewMode`, 'normal')
]

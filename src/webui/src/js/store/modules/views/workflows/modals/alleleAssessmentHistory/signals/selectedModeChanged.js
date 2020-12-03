import { set, equals } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'

export default [
    set(state`views.workflows.modals.alleleAssessmentHistory.selectedMode`, props`selectedMode`),
    equals(props`selectedMode`),
    {
        classification: [
            set(
                state`views.workflows.modals.alleleAssessmentHistory.selected`,
                state`views.workflows.modals.alleleAssessmentHistory.data.alleleassessments.0`
            )
        ],
        report: [
            set(
                state`views.workflows.modals.alleleAssessmentHistory.selected`,
                state`views.workflows.modals.alleleAssessmentHistory.data.allelereports.0`
            )
        ]
    }
]

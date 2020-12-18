import { set, equals } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'

export default [
    set(state`views.workflows.modals.alleleHistory.selectedMode`, props`selectedMode`),
    equals(props`selectedMode`),
    {
        classification: [
            set(
                state`views.workflows.modals.alleleHistory.selected`,
                state`views.workflows.modals.alleleHistory.data.alleleassessments.0`
            )
        ],
        report: [
            set(
                state`views.workflows.modals.alleleHistory.selected`,
                state`views.workflows.modals.alleleHistory.data.allelereports.0`
            )
        ]
    }
]

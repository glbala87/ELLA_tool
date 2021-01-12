/* jshint esnext: true */

import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'
import shouldShowSidebar from '../../store/modules/views/workflows/alleleSidebar/computed/shouldShowSidebar'

import template from './workflow.ngtmpl.html' // eslint-disable-line no-unused-vars

const showHistoricalDataWarning = Compute(
    state`views.workflows.type`,
    state`views.workflows.data.interpretations`,
    state`views.workflows.interpretation.selectedId`,
    state`views.workflows.interpretation.isOngoing`,
    (workflowType, interpretations, selectedInterpretationId, isOngoing) => {
        const result = {
            show: false,
            text: null
        }
        if (!workflowType || !interpretations || !selectedInterpretationId || isOngoing) {
            return result
        }

        let doneInterpretations = interpretations.filter((i) => i.status === 'Done')
        if (!doneInterpretations.length) {
            return result
        }

        if (selectedInterpretationId !== 'current') {
            const selectedInterpretation = interpretations.find(
                (i) => i.id === selectedInterpretationId
            )
            const analysisAddition =
                workflowType === 'analysis'
                    ? "Select 'Current data' above to see results with the latest annotation and filter configurations."
                    : ''
            const selectedDate = selectedInterpretation
                ? selectedInterpretation.date_last_update.split('T')[0]
                : '??-??-??'

            result.show = true
            result.text = `Data shown is from an interpretation performed ${selectedDate}. ${analysisAddition}`
        }

        return result
    }
)

app.component('workflow', {
    templateUrl: 'workflow.ngtmpl.html',
    controller: connect(
        {
            loaded: state`views.workflows.loaded`,
            showHistoricalDataWarning,
            showSidebar: shouldShowSidebar
        },
        'Workflow'
    )
})

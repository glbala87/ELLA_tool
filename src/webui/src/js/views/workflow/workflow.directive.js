/* jshint esnext: true */

import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'
import shouldShowSidebar from '../../store/modules/views/workflows/alleleSidebar/computed/shouldShowSidebar'
import getSelectedInterpretation from '../../store/modules/views/workflows/computed/getSelectedInterpretation'

import template from './workflow.ngtmpl.html' // eslint-disable-line no-unused-vars

const showHistoricalDataWarning = Compute(
    state`views.workflows.type`,
    state`views.workflows.data.interpretations`,
    state`views.workflows.interpretation.selectedId`,
    (workflowType, interpretations, selectedInterpretationId) => {
        const result = {
            show: false,
            date: null
        }
        if (!workflowType || !interpretations || !selectedInterpretationId) {
            return result
        }
        const latestInterpretation = interpretations[interpretations.length - 1]
        const selectedInterpretation = interpretations.find(
            (i) => i.id === selectedInterpretationId
        )
        result.show = selectedInterpretationId !== 'current' && latestInterpretation.finalized

        const analysisAddition =
            workflowType === 'analysis'
                ? "Select 'Current data' above to see results with the latest annotation and filter configurations."
                : ''
        const selectedDate = selectedInterpretation
            ? selectedInterpretation.date_last_update.split('T')[0]
            : '??-??-??'
        result.text = `Data shown is from an interpretation performed
        ${selectedDate}. ${analysisAddition}`
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

import { sequence, parallel } from 'cerebral'
import { set, wait } from 'cerebral/operators'
import { state, props, string } from 'cerebral/tags'
import getAnalysis from '../actions/getAnalysis'
import prepareComponents from '../actions/prepareComponents'
import loadInterpretations from '../sequences/loadInterpretations'
import loadInterpretationLogs from '../worklog/sequences/loadInterpretationLogs'
import toast from '../../../../common/factories/toast'
import { enableOnBeforeUnload } from '../../../../common/factories/onBeforeUnload'
import showExitWarning from '../showExitWarning'
import setNavbarTitle from '../../../../common/factories/setNavbarTitle'
import progress from '../../../../common/factories/progress'
import getWorkflowTitle from '../computed/getWorkflowTitle'
import prepareSelectedAllele from '../alleleSidebar/actions/prepareSelectedAllele'
import loadVisualization from '../visualization/sequences/loadVisualization'

const EXIT_WARNING = 'You have unsaved work. Do you really want to exit application?'

export default [
    progress('start'),
    enableOnBeforeUnload(showExitWarning, EXIT_WARNING),
    set(state`views.workflows.type`, string`analysis`),
    ({ state, props }) => {
        state.set('views.workflows.id', parseInt(props.analysisId))
    },
    sequence('loadAnalysis', [
        getAnalysis,
        {
            error: [toast('error', 'Failed to load analysis', 30000)],
            success: [
                set(state`views.workflows.data.analysis`, props`result`),
                ({ state }) => {
                    const analysis = state.get('views.workflows.data.analysis')
                    state.set('views.workflows.selectedGenepanel', {
                        name: analysis.genepanel.name,
                        version: analysis.genepanel.version
                    })
                },
                loadInterpretations,
                setNavbarTitle(getWorkflowTitle),
                parallel([
                    loadVisualization,
                    [
                        loadInterpretationLogs,
                        // Interpretation logs are needed in prepareComponents for analysis
                        prepareComponents,
                        prepareSelectedAllele
                    ]
                ])
            ]
        }
    ]),

    progress('done')
]

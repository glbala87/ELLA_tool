import { parallel, sequence } from 'cerebral'
import { set, when } from 'cerebral/operators'
import { props, state, string } from 'cerebral/tags'
import { enableOnBeforeUnload } from '../../../../common/factories/onBeforeUnload'
import progress from '../../../../common/factories/progress'
import setNavbarTitle from '../../../../common/factories/setNavbarTitle'
import toast from '../../../../common/factories/toast'
import getAnalysis from '../actions/getAnalysis'
import getAnalysisStats from '../actions/getAnalysisStats'
import prepareSelectedAllele from '../alleleSidebar/actions/prepareSelectedAllele'
import getWorkflowTitle from '../computed/getWorkflowTitle'
import loadInterpretations from '../sequences/loadInterpretations'
import showExitWarning from '../showExitWarning'
import loadVisualization from '../visualization/sequences/loadVisualization'
import selectedAlleleChanged from '../sequences/selectedAlleleChanged'

const EXIT_WARNING = 'You have unsaved work. Do you really want to exit application?'

export default [
    progress('start'),
    enableOnBeforeUnload(showExitWarning, EXIT_WARNING),
    set(state`views.workflows.type`, string`analysis`),
    ({ state, props }) => {
        state.set('views.workflows.id', parseInt(props.analysisId))
    },
    sequence('loadAnalysis', [
        getAnalysisStats,
        {
            error: [toast('error', 'Failed to load analysis stats', 30000)],
            success: [
                set(state`views.workflows.data.stats`, props`result`),
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
                                prepareSelectedAllele,
                                when(state`views.workflows.selectedAllele`),
                                {
                                    true: [
                                        set(props`alleleId`, state`views.workflows.selectedAllele`),
                                        selectedAlleleChanged
                                    ],
                                    false: []
                                }
                            ]
                        ])
                    ]
                }
            ]
        }
    ]),

    progress('done')
]

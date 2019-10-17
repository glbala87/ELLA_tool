import { set, when } from 'cerebral/operators'
import { state, props, string } from 'cerebral/tags'
import getAlleleByIdentifier from '../actions/getAlleleByIdentifier'
import getGenepanels from '../actions/getGenepanels'
import prepareComponents from '../actions/prepareComponents'
import loadInterpretations from '../sequences/loadInterpretations'
import toast from '../../../../common/factories/toast'
import loadInterpretationLogs from '../worklog/sequences/loadInterpretationLogs'
import showExitWarning from '../showExitWarning'
import { enableOnBeforeUnload } from '../../../../common/factories/onBeforeUnload'
import setNavbarTitle from '../../../../common/factories/setNavbarTitle'
import getWorkflowTitle from '../computed/getWorkflowTitle'

const EXIT_WARNING = 'You have unsaved work. Do you really want to exit application?'

export default [
    setNavbarTitle(' '),
    enableOnBeforeUnload(showExitWarning, EXIT_WARNING),
    set(state`views.workflows.type`, string`allele`),
    getAlleleByIdentifier,
    {
        error: [toast('error', 'Invalid URL: Variant not found')],
        success: [
            set(state`views.workflows.allele`, props`result`),
            set(state`views.workflows.id`, props`result.id`),
            when(props`query.gp_name`), // If no genepanel is provided, we need to get a list of options
            {
                true: [
                    ({ props, state }) => {
                        state.set('views.workflows.selectedGenepanel', {
                            name: props.query.gp_name,
                            version: props.query.gp_version
                        })
                    }
                ],
                false: [
                    getGenepanels,
                    {
                        success: [
                            set(state`views.workflows.data.genepanels`, props`result`),
                            // Select first genepanel by default
                            set(
                                state`views.workflows.selectedGenepanel`,
                                state`views.workflows.data.genepanels.0`
                            )
                        ],
                        error: [toast('error', 'Failed to load genepanels')]
                    }
                ]
            },
            prepareComponents,
            loadInterpretations,
            // We need the formatted allele, so postpone setting title until here.
            setNavbarTitle(getWorkflowTitle)
        ]
    },
    // For allele we can postpone loading interpretation logs until end
    loadInterpretationLogs
]

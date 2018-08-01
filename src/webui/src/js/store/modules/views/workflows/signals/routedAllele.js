import { parallel } from 'cerebral'
import { set, when } from 'cerebral/operators'
import { state, props, string } from 'cerebral/tags'
import getAlleleByIdentifier from '../actions/getAlleleByIdentifier'
import getGenepanels from '../actions/getGenepanels'
import prepareComponents from '../actions/prepareComponents'
import loadInterpretations from '../sequences/loadInterpretations'
import toast from '../../../../common/factories/toast'
import loadGenepanel from '../sequences/loadGenepanel'
import loadCollisions from '../sequences/loadCollisions'
import showExitWarning from '../showExitWarning'
import { enableOnBeforeUnload } from '../../../../common/factories/onBeforeUnload'
import setNavbarTitle from '../../../../common/factories/setNavbarTitle'

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
            when(props`gp`), // If no genepanel is provided, we need to get a list of options
            {
                true: [
                    // Rename props (strange format, see: https://github.com/cerebral/cerebral/issues/1181 )
                    ({ props, state }) => {
                        state.set('views.workflows.selectedGenepanel', {
                            name: props.gp.name,
                            version: props.gp.gp.version
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
            loadGenepanel,
            prepareComponents,
            parallel([
                [
                    loadInterpretations,
                    // We need the formatted allele, so postpone setting title until here.
                    setNavbarTitle(
                        string`${state`views.workflows.data.alleles.${state`views.workflows.id`}.formatted.display`} (${state`views.workflows.selectedGenepanel.name`}_${state`views.workflows.selectedGenepanel.version`})`
                    )
                ],
                loadCollisions
            ])
        ]
    }
]

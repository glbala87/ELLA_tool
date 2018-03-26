import { parallel, sequence } from 'cerebral'
import { set, equals } from 'cerebral/operators'
import { state, props, string } from 'cerebral/tags'
import { redirect } from '@cerebral/router/operators'
import { HttpProviderError } from '@cerebral/http'
import getAlleleByIdentifer from '../actions/getAlleleByIdentifier'
import getAnalysis from '../actions/getAnalysis'
import getGenepanel from '../actions/getGenepanel'
import getCollisions from '../actions/getCollisions'
import prepareComponents from '../actions/prepareComponents'
import loadInterpretations from '../sequences/loadInterpretations'
import loadGenepanel from '../sequences/loadGenepanel'
import toastr from '../../../../common/factories/toastr'
import { enableOnBeforeUnload } from '../../../../common/factories/onBeforeUnload'
import showExitWarning from '../showExitWarning'
import loadCollisions from '../sequences/loadCollisions'
import setNavbarTitle from '../../../../common/factories/setNavbarTitle'
import addExcludedAllelesClicked from '../../../modals/addExcludedAlleles/signals/addExcludedAllelesClicked'
import isReadOnly from '../computed/isReadOnly'

const EXIT_WARNING = 'You have unsaved work. Do you really want to exit application?'

export default [
    enableOnBeforeUnload(showExitWarning, EXIT_WARNING),
    set(state`views.workflows.type`, string`analysis`),
    ({ state, props }) => {
        state.set('views.workflows.id', parseInt(props.analysisId))
    },
    parallel([
        sequence('loadAnalysis', [
            getAnalysis,
            {
                error: [toastr('error', 'Failed to load analysis', 30000)],
                success: [
                    set(state`views.workflows.data.analysis`, props`result`),
                    setNavbarTitle(state`views.workflows.data.analysis.name`),
                    prepareComponents,
                    ({ state, props }) => {
                        const analysis = state.get('views.workflows.data.analysis')
                        state.set('views.workflows.selectedGenepanel', {
                            name: analysis.genepanel.name,
                            version: analysis.genepanel.version
                        })
                    },
                    loadGenepanel,
                    loadInterpretations
                ]
            }
        ]),
        loadCollisions
    ])
]

import { parallel } from 'cerebral'
import { set, equals } from 'cerebral/operators'
import { state, props, string } from 'cerebral/tags'
import { redirect } from '@cerebral/router/operators'
import { HttpProviderError } from '@cerebral/http'
import getAlleleByIdentifier from '../actions/getAlleleByIdentifier'
import getGenepanel from '../actions/getGenepanel'
import getCollisions from '../actions/getCollisions'
import prepareComponents from '../actions/prepareComponents'
import loadInterpretations from '../sequences/loadInterpretations'
import toastr from '../../../../common/factories/toastr'
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
    // Rename props (strange format, see: https://github.com/cerebral/cerebral/issues/1181 )
    set(props`genepanelName`, props`gp.name`),
    set(props`genepanelVersion`, props`gp.gp.version`),
    getAlleleByIdentifier,
    {
        error: [toastr('error', 'Invalid address: Variant not found', 3000000)],
        success: [
            set(state`views.workflows.allele`, props`result`),
            set(state`views.workflows.id`, props`result.id`),
            loadGenepanel,
            prepareComponents,
            parallel([
                [
                    loadInterpretations,
                    // We need the formatted allele, so postpone setting title until here.
                    setNavbarTitle(
                        state`views.workflows.data.alleles.${state`views.workflows.id`}.formatted.hgvsc`
                    )
                ],
                loadCollisions
            ])
        ]
    }
]

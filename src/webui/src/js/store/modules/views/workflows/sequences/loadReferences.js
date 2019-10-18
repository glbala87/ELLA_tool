import { sequence } from 'cerebral'
import { set } from 'cerebral/operators'
import { props, state } from 'cerebral/tags'
import toast from '../../../../common/factories/toast'
import getReferences from '../actions/getReferences'
import autoIgnoreReferences from '../../workflows/interpretation/actions/autoIgnoreReferences'

export default sequence('loadReferences', [
    getReferences,
    {
        success: [
            set(state`views.workflows.interpretation.data.references`, props`result`),
            autoIgnoreReferences
        ],
        error: [toast('error', 'Failed to load references', 30000)]
    }
])

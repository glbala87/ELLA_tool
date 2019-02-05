import { sequence } from 'cerebral'
import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import getAlleles from '../actions/getAlleles'
import toast from '../../../../../../common/factories/toast'

export default sequence('loadIncludedAlleles', [
    set(props`alleleIds`, state`views.workflows.modals.addExcludedAlleles.includedAlleleIds`),
    getAlleles,
    {
        success: [
            set(
                state`views.workflows.modals.addExcludedAlleles.data.includedAlleles`,
                props`result`
            )
        ],
        error: [toast('error', 'Failed to load included variants')]
    }
])

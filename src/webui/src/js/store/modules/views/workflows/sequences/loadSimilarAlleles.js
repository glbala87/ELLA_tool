import { sequence } from 'cerebral'
import { set } from 'cerebral/operators'
import { props, state } from 'cerebral/tags'
import toast from '../../../../common/factories/toast'
import loadSimilarAlleles from '../actions/getSimilarAlleles'

export default sequence('loadSimilarAlleles', [
    loadSimilarAlleles,
    {
        success: [
            ({ props, state }) => {
                state.set(`views.workflows.interpretation.data.similar`, props.result)
            }
        ],
        error: [toast('error', 'Failed to load similar variants', 30000)]
    }
])

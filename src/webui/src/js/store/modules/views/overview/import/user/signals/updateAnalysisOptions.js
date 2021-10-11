import { props, state } from 'cerebral/tags'
import { set } from 'cerebral/operators'
import getAnalyses from '../actions/getAnalyses'
import toast from '../../../../../../common/factories/toast'

export default [
    set(props`perPage`, 20),
    getAnalyses,
    {
        success: [
            set(
                state`views.overview.import.user.jobData.${props`index`}.analysesOptions`,
                props`result`
            )
        ],
        error: [toast('error', 'Failed to search for analyses')]
    }
]

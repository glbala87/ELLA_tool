import { set } from 'cerebral/operators'
import { props } from 'cerebral/tags'
import toast from '../../../../../common/factories/toast'

export default [
    ({ state, clipboard }) => {
        clipboard.copy(state.get('views.overview.import.custom.candidates.filterBatch'))
    },
    toast('info', `Copied missing genes to clipboard`)
]

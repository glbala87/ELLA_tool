import { when, set, debounce } from 'cerebral/operators'
import { state, module, props } from 'cerebral/tags'
import toastr from '../../../../../common/factories/toastr'
import canUpdateReferenceAssessment from '../operators/canUpdateReferenceAssessment'
import setReferenceAssessment from '../actions/setReferenceAssessment'
import setDirty from '../actions/setDirty'

export default [
    canUpdateReferenceAssessment,
    {
        true: [setDirty, set(props`evaluation`, { relevance: 'Ignore' }), setReferenceAssessment],
        false: [
            toastr('error', 'Cannot update reference evaluation when interpretation is not Ongoing')
        ]
    }
]

import { debounce } from 'cerebral/operators'
import setDirty from '../actions/setDirty'
import canUpdateAlleleAssessment from '../operators/canUpdateAlleleAssessment'
import setReferenceAssessment from '../actions/setReferenceAssessment'

export default [
    debounce(200),
    {
        continue: [
            canUpdateAlleleAssessment,
            {
                true: [setDirty, setReferenceAssessment],
                false: []
            }
        ],
        discard: []
    }
]

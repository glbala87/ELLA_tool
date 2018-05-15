import { when, set, debounce } from 'cerebral/operators'
import { state, string, props } from 'cerebral/tags'
import canUpdateAlleleAssessment from '../operators/canUpdateAlleleAssessment'
import toastr from '../../../../../common/factories/toastr'
import showReferenceEvalModal from '../actions/showReferenceEvalModal'
import setReferenceAssessment from '../actions/setReferenceAssessment'
import postCustomAnnotation from '../actions/postCustomAnnotation'
import loadReferences from '../../sequences/loadReferences'
import loadAcmg from '../../sequences/loadAcmg'
import setDirty from '../actions/setDirty'

export default [
    showReferenceEvalModal,
    {
        result: [
            canUpdateAlleleAssessment,
            {
                true: [setDirty, setReferenceAssessment, loadAcmg],
                false: [toastr('error', string`Could not add ${props`category`} annotation`)]
            }
        ],
        dismissed: []
    }
]

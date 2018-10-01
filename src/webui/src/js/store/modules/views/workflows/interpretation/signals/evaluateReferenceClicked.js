import { when, set, debounce } from 'cerebral/operators'
import { state, string, props } from 'cerebral/tags'
import canUpdateAlleleAssessment from '../operators/canUpdateAlleleAssessment'
import toast from '../../../../../common/factories/toast'
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
                false: [toast('error', string`Could not add ${props`category`} annotation`)]
            }
        ],
        dismissed: []
    }
]

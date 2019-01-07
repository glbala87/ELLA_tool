import { props, string } from 'cerebral/tags';
import toast from '../../../../../common/factories/toast';
import loadAcmg from '../../sequences/loadAcmg';
import setDirty from '../actions/setDirty';
import setReferenceAssessment from '../actions/setReferenceAssessment';
import showReferenceEvalModal from '../actions/showReferenceEvalModal';
import canUpdateAlleleAssessment from '../operators/canUpdateAlleleAssessment';

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

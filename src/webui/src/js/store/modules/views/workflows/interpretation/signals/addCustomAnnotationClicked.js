import { when } from 'cerebral/operators';
import { props, string } from 'cerebral/tags';
import toast from '../../../../../common/factories/toast';
import loadAcmg from '../../sequences/loadAcmg';
import loadAlleles from '../../sequences/loadAlleles';
import loadReferences from '../../sequences/loadReferences';
import postCustomAnnotation from '../actions/postCustomAnnotation';
import setDirty from '../actions/setDirty';
import showCustomAnnotationModal from '../actions/showCustomAnnotationModal';
import canUpdateAlleleAssessment from '../operators/canUpdateAlleleAssessment';

export default [
    showCustomAnnotationModal,
    {
        result: [
            canUpdateAlleleAssessment,
            {
                true: [
                    postCustomAnnotation,
                    {
                        success: [
                            setDirty,
                            loadAlleles,
                            loadAcmg,
                            when(props`category`, (c) => c === 'references'),
                            {
                                true: loadReferences,
                                false: [] // noop
                            }
                        ],
                        error: [
                            toast('error', string`Could not submit ${props`category`} annotation`)
                        ]
                    }
                ],
                false: [toast('error', string`Could not add ${props`category`} annotation`)]
            }
        ],
        dismissed: []
    }
]

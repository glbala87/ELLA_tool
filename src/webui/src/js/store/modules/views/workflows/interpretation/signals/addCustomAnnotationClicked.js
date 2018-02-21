import { when, set, debounce } from 'cerebral/operators'
import { state, string, props } from 'cerebral/tags'
import canUpdateAlleleAssessment from '../operators/canUpdateAlleleAssessment'
import toastr from '../../../../../common/factories/toastr'
import showCustomAnnotationModal from '../actions/showCustomAnnotationModal'
import postCustomAnnotation from '../actions/postCustomAnnotation'
import loadAlleles from '../../sequences/loadAlleles'
import loadReferences from '../../sequences/loadReferences'
import setDirty from '../actions/setDirty'
import loadAcmg from '../../sequences/loadAcmg'

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
                            when(props`category`, c => c === 'references'),
                            {
                                true: loadReferences,
                                false: [] // noop
                            }
                        ],
                        error: [
                            toastr('error', string`Could not submit ${props`category`} annotation`)
                        ]
                    }
                ],
                false: [toastr('error', string`Could not add ${props`category`} annotation`)]
            }
        ],
        dismissed: []
    }
]

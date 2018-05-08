import { when, set, toggle } from 'cerebral/operators'
import { state, module, props } from 'cerebral/tags'
import isAlleleAssessmentOutdated from '../operators/isAlleleAssessmentOutdated'
import toggleReuseReferenceAssessments from '../actions/toggleReuseReferenceAssessments'
import toastr from '../../../../../common/factories/toastr'
import setDirty from '../actions/setDirty'
import toggleReuseAlleleAssessment from '../actions/toggleReuseAlleleAssessment'
import copyExistingAlleleAssessments from '../../actions/copyExistingAlleleAssessments'
import autoReuseExistingReferenceAssessments from '../actions/autoReuseExistingReferenceAssessments'

export default [
    isAlleleAssessmentOutdated,
    {
        true: [toastr('error', 'Cannot toggle reuse of outdated classification')],
        false: [
            toggleReuseAlleleAssessment,
            copyExistingAlleleAssessments,
            set(
                state`views.workflows.interpretation.selected.state.allele.${props`alleleId`}.referenceassessments`,
                []
            ),
            autoReuseExistingReferenceAssessments
        ]
    }
]

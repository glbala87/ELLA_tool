import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import toggleReuseAlleleAssessment from '../actions/toggleReuseAlleleAssessment'
import copyExistingAlleleAssessments from '../../actions/copyExistingAlleleAssessments'
import autoReuseExistingReferenceAssessments from '../actions/autoReuseExistingReferenceAssessments'
import isReadOnly from '../operators/isReadOnly'

export default [
    isReadOnly,
    {
        false: [
            toggleReuseAlleleAssessment,
            copyExistingAlleleAssessments,
            set(
                state`views.workflows.interpretation.state.allele.${props`alleleId`}.referenceassessments`,
                []
            ),
            autoReuseExistingReferenceAssessments
        ],
        true: []
    }
]

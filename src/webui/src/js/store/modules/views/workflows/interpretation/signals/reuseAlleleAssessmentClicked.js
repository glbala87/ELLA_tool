import { set, when } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import toggleReuseAlleleAssessment from '../actions/toggleReuseAlleleAssessment'
import copyExistingAlleleAssessments from '../../actions/copyExistingAlleleAssessments'
import autoReuseExistingReferenceAssessments from '../actions/autoReuseExistingReferenceAssessments'
import isReadOnly from '../operators/isReadOnly'
import allelesChanged from '../../alleleSidebar/sequences/allelesChanged';

export default [
    isReadOnly,
    {
        false: [
            toggleReuseAlleleAssessment,
            copyExistingAlleleAssessments,
            // resets dropdown in UI, but causes problem with unit tests.
            // `classification: null` prevents the re-filling of data and so can't be finalized
            when(state`views.workflows.interpretation.state.allele.${props`alleleId`}.alleleassessment.reuse`),
            {
                true: [],
                false: [
                    set(
                        state`views.workflows.interpretation.state.allele.${props`alleleId`}.alleleassessment.classification`,
                        null
                    )
                ]
            },
            set(
                state`views.workflows.interpretation.state.allele.${props`alleleId`}.referenceassessments`,
                []
            ),
            autoReuseExistingReferenceAssessments,
            allelesChanged
        ],
        true: []
    }
]

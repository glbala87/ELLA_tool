import { sequence } from 'cerebral'
import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import canUpdateAlleleAssessment from '../operators/canUpdateAlleleAssessment'
import setDirty from '../actions/setDirty'
import getSuggestedClassification from '../actions/getSuggestedClassification'
import toast from '../../../../../common/factories/toast'

export default sequence('updateSuggestedClassification', [
    canUpdateAlleleAssessment,
    {
        true: [
            getSuggestedClassification,
            {
                success: [
                    set(
                        state`views.workflows.interpretation.selected.state.allele.${props`alleleId`}.alleleassessment.evaluation.acmg.suggested_classification`,
                        props`result.class`
                    ),
                    setDirty
                ],
                aborted: [],
                error: [toast('error', 'Failed to load suggested classification')]
            }
        ],
        false: [] // noop
    }
])

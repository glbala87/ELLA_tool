import { debounce, set } from 'cerebral/operators'
import { module, props } from 'cerebral/tags'
import toast from '../../../../../common/factories/toast'
import setDirty from '../actions/setDirty'
import canUpdateAlleleAssessment from '../operators/canUpdateAlleleAssessment'

export default [
    debounce(200),
    {
        continue: [
            canUpdateAlleleAssessment,
            {
                true: [
                    setDirty,
                    set(
                        module`state.allele.${props`alleleId`}.alleleassessment.evaluation.${props`name`}.comment`,
                        props`comment`
                    )
                ],
                false: []
            }
        ],
        discard: []
    }
]

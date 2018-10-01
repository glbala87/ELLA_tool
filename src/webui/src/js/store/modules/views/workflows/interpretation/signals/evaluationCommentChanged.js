import { when, set, debounce } from 'cerebral/operators'
import { state, module, props } from 'cerebral/tags'
import canUpdateAlleleAssessment from '../operators/canUpdateAlleleAssessment'
import toast from '../../../../../common/factories/toast'
import setDirty from '../actions/setDirty'

export default [
    debounce(200),
    {
        continue: [
            canUpdateAlleleAssessment,
            {
                true: [
                    setDirty,
                    set(
                        module`selected.state.allele.${props`alleleId`}.alleleassessment.evaluation.${props`name`}.comment`,
                        props`comment`
                    )
                ],
                false: [
                    toast(
                        'error',
                        'Cannot change evaluation comment when interpretation is not Ongoing'
                    )
                ]
            }
        ],
        discard: []
    }
]

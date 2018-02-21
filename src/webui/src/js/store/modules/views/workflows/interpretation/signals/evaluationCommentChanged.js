import { when, set, debounce } from 'cerebral/operators'
import { state, module, props } from 'cerebral/tags'
import canUpdateAlleleAssessment from '../operators/canUpdateAlleleAssessment'
import toastr from '../../../../../common/factories/toastr'
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
                    toastr(
                        'error',
                        'Cannot change evaluation comment when interpretation is not Ongoing'
                    )
                ]
            }
        ],
        discard: []
    }
]

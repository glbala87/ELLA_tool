import { when, set, debounce } from 'cerebral/operators'
import { state, module, props } from 'cerebral/tags'
import canUpdateAlleleReport from '../operators/canUpdateAlleleReport'
import toast from '../../../../../common/factories/toast'
import setDirty from '../actions/setDirty'

export default [
    debounce(200),
    {
        continue: [
            canUpdateAlleleReport,
            {
                true: [
                    setDirty,
                    set(
                        module`selected.state.allele.${props`alleleId`}.allelereport.evaluation.comment`,
                        props`comment`
                    )
                ],
                false: [
                    toast(
                        'error',
                        'Cannot change report comment when interpretation is not Ongoing'
                    )
                ]
            }
        ],
        discard: []
    }
]

import { debounce, set } from 'cerebral/operators'
import { module, props } from 'cerebral/tags'
import toast from '../../../../../common/factories/toast'
import setDirty from '../actions/setDirty'
import canUpdateAlleleReport from '../operators/canUpdateAlleleReport'

export default [
    debounce(200),
    {
        continue: [
            canUpdateAlleleReport,
            {
                true: [
                    setDirty,
                    set(
                        module`state.allele.${props`alleleId`}.allelereport.evaluation.comment`,
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

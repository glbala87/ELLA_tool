import { set, debounce } from 'cerebral/operators'
import { module, props } from 'cerebral/tags'
import canUpdateAlleleReport from '../operators/canUpdateAlleleReport'
import toast from '../../../../../common/factories/toast'
import setDirty from '../actions/setDirty'

export default [
    debounce(200),
    {
        continue: [
            canUpdateAlleleReport, // Quality updates follows rules for allele report
            {
                true: [
                    setDirty,
                    set(
                        module`selected.state.allele.${props`alleleId`}.quality.comment`,
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

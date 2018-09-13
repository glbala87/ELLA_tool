import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import canUpdateAlleleAssessment from '../operators/canUpdateAlleleAssessment'
import toast from '../../../../../common/factories/toast'
import checkAddRemoveAlleleToReport from '../actions/checkAddRemoveAllelesToReport'
import allelesChanged from '../../alleleSidebar/sequences/allelesChanged'
import setDirty from '../actions/setDirty'

export default [
    canUpdateAlleleAssessment,
    {
        true: [
            setDirty,
            set(
                state`views.workflows.interpretation.selected.state.allele.${props`alleleId`}.alleleassessment.classification`,
                props`classification`
            ),
            // Prepare props for checkAddRemoveAlleleToReport
            ({ props }) => {
                return {
                    checkReportAlleleIds: [props.alleleId]
                }
            },
            checkAddRemoveAlleleToReport,
            allelesChanged
        ],
        false: [toast('error', 'Cannot change classification when interpretation is not Ongoing')]
    }
]

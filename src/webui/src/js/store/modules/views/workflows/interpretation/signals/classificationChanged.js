import { when, set, debounce } from 'cerebral/operators'
import { state, module, props } from 'cerebral/tags'
import canUpdateAlleleAssessment from '../operators/canUpdateAlleleAssessment'
import toastr from '../../../../../common/factories/toastr'
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
        false: [toastr('error', 'Cannot change classification when interpretation is not Ongoing')]
    }
]

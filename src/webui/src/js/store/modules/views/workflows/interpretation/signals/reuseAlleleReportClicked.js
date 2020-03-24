import isReadOnly from '../operators/isReadOnly'
import canUpdateAlleleReport from '../operators/canUpdateAlleleReport'
import { deepCopy } from '../../../../../../util'

function copyAlleleReport({ state, props }) {
    const { alleleId } = props
    const allele = state.get(`views.workflows.interpretation.data.alleles.${alleleId}`)
    state.set(
        `views.workflows.interpretation.state.allele.${alleleId}.allelereport.evaluation.comment`,
        allele.allele_report.evaluation.comment
    )
}

export default [
    isReadOnly,
    {
        false: [
            canUpdateAlleleReport,
            {
                true: [copyAlleleReport],
                false: []
            }
        ],
        true: []
    }
]

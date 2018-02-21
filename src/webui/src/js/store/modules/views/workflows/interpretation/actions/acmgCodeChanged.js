import { deepCopy } from '../../../../../../util'

export default function acmgCodeChanged({ state, props }) {
    const { alleleId, code } = props

    const included = state.get(
        `views.workflows.interpretation.selected.state.allele.${alleleId}.alleleassessment.evaluation.acmg.included`
    )
    const idx = included.findIndex(c => c.uuid === code.uuid)

    state.merge(
        `views.workflows.interpretation.selected.state.allele.${alleleId}.alleleassessment.evaluation.acmg.included.${idx}`,
        code
    )
}

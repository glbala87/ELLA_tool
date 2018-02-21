import { UUID } from '../../../../../../util'

export default function addAcmgCode({ state, props }) {
    const { alleleId, code } = props

    const included = state.get(
        `views.workflows.interpretation.selected.state.allele.${alleleId}.alleleassessment.evaluation.acmg.included`
    )
    const idx = included.findIndex(c => c.uuid === code.uuid)

    if (idx < 0) {
        throw Error(`Code ${code.uuid} not found in included codes`)
    }

    state.splice(
        `views.workflows.interpretation.selected.state.allele.${alleleId}.alleleassessment.evaluation.acmg.included`,
        idx,
        1
    )
}

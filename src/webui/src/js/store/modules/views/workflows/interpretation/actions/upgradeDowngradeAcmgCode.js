export default function upgradeDowngradeAcmgCode({ state, props }) {
    const { alleleId, uuid, upgrade } = props
    const included = state.get(
        `views.workflows.interpretation.selected.state.allele.${alleleId}.alleleassessment.evaluation.acmg.included`
    )
    const codeIdx = included.findIndex((v) => v.uuid === uuid)
    const config = state.get('app.config')

    if (codeIdx < 0) {
        throw Error(`ACMG code with UUID ${uuid} not found in included codes`)
    }

    const code = included[codeIdx]
    newCode = upgradeDowngradeAcmgCode(code.code, config, upgrade)
    state.set(
        `views.workflows.interpretation.selected.state.allele.${alleleId}.alleleassessment.evaluation.acmg.included.${codeIdx}.code`,
        newCode
    )
}

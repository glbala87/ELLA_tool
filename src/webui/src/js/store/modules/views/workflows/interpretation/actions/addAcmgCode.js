import { UUID } from '../../../../../../util'

export default function addAcmgCode({ state, props }) {
    const { alleleId, code } = props

    // Create code from props data
    const toInclude = {
        uuid: UUID(),
        code: code.code,
        match: code.match || null,
        op: code.op || null,
        source: code.source || null,
        comment: code.comment || ''
    }

    state.push(
        `views.workflows.interpretation.selected.state.allele.${alleleId}.alleleassessment.evaluation.acmg.included`,
        toInclude
    )
}

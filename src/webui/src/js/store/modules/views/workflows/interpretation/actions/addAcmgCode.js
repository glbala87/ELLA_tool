import { UUID } from '../../../../../../util'
import { containsCodeBase } from '../../../../../common/helpers/acmg'

export default function addAcmgCode({ state, props }) {
    const { alleleId, code } = props

    // Check that code is not added already

    const added = state.get(
        `views.workflows.interpretation.state.allele.${alleleId}.alleleassessment.evaluation.acmg.included`
    )
    if (containsCodeBase(added, code.code)) {
        throw Error(`Code (or base of) ${code.code} is already added`)
    }

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
        `views.workflows.interpretation.state.allele.${alleleId}.alleleassessment.evaluation.acmg.included`,
        toInclude
    )
}

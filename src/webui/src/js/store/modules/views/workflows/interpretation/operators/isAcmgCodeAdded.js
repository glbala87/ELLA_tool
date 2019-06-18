import { containsCodeBase } from '../../../../../common/helpers/acmg'

export default function isAcmgCodeAdded({ state, path, props }) {
    if (!props.alleleId) {
        throw Error('Missing required props alleleId')
    }
    if (!props.code) {
        throw Error('Missing required props code')
    }
    const { alleleId, code } = props
    const added = state.get(
        `views.workflows.interpretation.state.allele.${alleleId}.alleleassessment.evaluation.acmg.included`
    )
    return containsCodeBase(added, code.code) ? path.true() : path.false()
}

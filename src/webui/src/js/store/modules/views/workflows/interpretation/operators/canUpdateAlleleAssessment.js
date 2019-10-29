import isReadOnly from '../../computed/isReadOnly'

export default function canUpdateAlleleAssessment({ state, path, props, resolve }) {
    if (!props.alleleId) {
        throw Error('Missing required props alleleId')
    }
    if (
        !resolve.value(isReadOnly) &&
        !state.get(
            `views.workflows.interpretation.state.allele.${props.alleleId}.alleleassessment.reuse`
        )
    ) {
        return path.true()
    }
    return path.false()
}

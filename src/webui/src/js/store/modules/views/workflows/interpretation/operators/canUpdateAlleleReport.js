export default function canUpdateAlleleReport({ state, path, props }) {
    if (!props.alleleId) {
        throw Error('Missing required props alleleId')
    }
    if (
        state.get('views.workflows.interpretation.isOngoing') &&
        !state.get(
            `views.workflows.interpretation.state.allele.${props.alleleId}.allelereport.reuse`
        )
    ) {
        return path.true()
    }
    return path.false()
}

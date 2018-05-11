export default function canUpdateAlleleAssessment({ state, path, props }) {
    if (!props.alleleId) {
        throw Error('Missing required props alleleId')
    }
    if (
        state.get('views.workflows.interpretation.isOngoing') &&
        !state.get(
            `views.workflows.interpretation.selected.state.allele.${
                props.alleleId
            }.alleleassessment.reuse`
        )
    ) {
        return path.true()
    }
    return path.false()
}

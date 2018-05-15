export default function canUpdateReferenceAssessment({ state, path, props }) {
    if (!props.alleleId) {
        throw Error('Missing required props alleleId')
    }
    if (!props.referenceId) {
        throw Error('Missing required props alleleId')
    }
    if (state.get('views.workflows.interpretation.isOngoing')) {
        return path.true()
    }
    return path.false()
}

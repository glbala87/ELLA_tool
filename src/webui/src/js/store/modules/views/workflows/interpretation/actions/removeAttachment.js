export default function removeAttachment({ state, props }) {
    const alleleState = state.get(`views.workflows.interpretation.state.allele.${props.alleleId}`)
    const { alleleId, attachmentId } = props
    const attachmentIdx = alleleState.alleleassessment.attachment_ids.findIndex(
        (a) => a === attachmentId
    )

    if (attachmentIdx >= 0) {
        state.splice(
            `views.workflows.interpretation.state.allele.${alleleId}.alleleassessment.attachment_ids`,
            attachmentIdx,
            1
        )
    } else {
        throw Error(
            `Couldn't find attachment with id ${attachmentId} in alleleassessment for allele id ${alleleId}`
        )
    }
}

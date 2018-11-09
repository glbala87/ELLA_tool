export default function setVerificationStatus({ props, state }) {
    const { alleleId, verificationStatus } = props
    state.set(
        `views.workflows.interpretation.selected.state.allele.${alleleId}.analysis.verification`,
        verificationStatus
    )
}

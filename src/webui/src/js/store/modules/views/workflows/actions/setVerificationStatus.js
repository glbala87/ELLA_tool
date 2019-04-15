export default function setVerificationStatus({ props, state }) {
    const { alleleId, verificationStatus } = props
    state.set(
        `views.workflows.interpretation.state.allele.${alleleId}.analysis.verification`,
        verificationStatus
    )
}

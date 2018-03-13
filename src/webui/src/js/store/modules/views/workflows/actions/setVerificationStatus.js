import { state } from 'cerebral/tags'
import sortAlleles from '../computed/sortAlleles'

export default function setVerificationStatus({ props, state }) {
    const { alleleId, verificationStatus } = props
    state.set(
        `views.workflows.interpretation.selected.state.allele.${alleleId}.verification`,
        verificationStatus
    )
}

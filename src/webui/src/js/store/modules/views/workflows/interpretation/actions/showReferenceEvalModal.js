import getReferenceAssessment from '../computed/getReferenceAssessment'
import isReadOnly from '../../computed/isReadOnly'

export default function showReferenceEvalModal({
    ReferenceEvalModal,
    props,
    state,
    path,
    resolve
}) {
    const analysis = state.get('views.workflows.data.analysis')
    const allele = state.get(`views.workflows.data.alleles.${props.alleleId}`)
    const reference = state.get(`views.workflows.data.references.${props.referenceId}`)
    const referenceAssessment = resolve.value(getReferenceAssessment(allele.id, reference.id)) || {}
    const readOnly = resolve.value(isReadOnly)

    return ReferenceEvalModal.show(analysis, allele, reference, referenceAssessment, readOnly)
        .then(result => {
            if (result) {
                return path.result({ evaluation: result.evaluation })
            }
            return path.dismissed()
        })
        .catch(result => {
            return path.dismissed()
        })
}

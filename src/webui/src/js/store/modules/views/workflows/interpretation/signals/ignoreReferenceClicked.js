import toast from '../../../../../common/factories/toast';
import setDirty from '../actions/setDirty';
import setReferenceAssessment from '../actions/setReferenceAssessment';
import getReferenceAssessment from '../computed/getReferenceAssessment';
import canUpdateReferenceAssessment from '../operators/canUpdateReferenceAssessment';


export default [
    canUpdateReferenceAssessment,
    {
        true: [
            ({ props, resolve }) => {
                const { alleleId, referenceId } = props
                const existingReferenceAssessment = resolve.value(
                    getReferenceAssessment(alleleId, referenceId)
                )
                const existingEvaluation = existingReferenceAssessment
                    ? existingReferenceAssessment.evaluation
                    : {}
                return {
                    evaluation: Object.assign({}, existingEvaluation, { relevance: 'Ignore' })
                }
            },
            setReferenceAssessment,
            setDirty
        ],
        false: [
            toast('error', 'Cannot update reference evaluation when interpretation is not Ongoing')
        ]
    }
]

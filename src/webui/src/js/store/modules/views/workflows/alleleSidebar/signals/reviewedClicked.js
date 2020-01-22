import { toggle, when } from 'cerebral/operators'
import { props, state } from 'cerebral/tags'
import setDirty from '../../interpretation/actions/setDirty'
import isReadOnly from '../../interpretation/operators/isReadOnly'
import getAlleleReviewedStatus from '../../interpretation/computed/getAlleleReviewedStatus'

function canMarkReview({ state, props, resolve, path }) {
    const alleleState = state.get('views.workflows.interpretation.state.allele')
    const alleleId = props.alleleId
    if (!(alleleId in alleleState)) {
        return path.false()
    }
    const allele = state.get(`views.workflows.interpretation.data.alleles.${alleleId}`)
    if (!allele) {
        return path.false()
    }
    const reviewStatus = resolve.value(getAlleleReviewedStatus(allele))
    if (reviewStatus === 'finalized') {
        return path.false()
    }
    return path.true()
}

export default [
    isReadOnly,
    {
        true: [],
        false: [
            canMarkReview,
            {
                true: [
                    toggle(
                        state`views.workflows.interpretation.state.allele.${props`alleleId`}.workflow.reviewed`
                    ),
                    setDirty
                ],
                false: []
            }
        ]
    }
]

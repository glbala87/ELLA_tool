import thenBy from 'thenby'
import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'

export default Compute(state`views.workflows.data.interpretationlogs`, (logs) => {
    if (!logs) {
        return null
    }
    const sortedReviewComment = Object.values(logs)
        .sort(thenBy('date_created', -1))
        .filter((l) => l.review_comment !== null)
        .map((l) => l.review_comment)

    if (sortedReviewComment.length) {
        return sortedReviewComment[0]
    }
    return null
})

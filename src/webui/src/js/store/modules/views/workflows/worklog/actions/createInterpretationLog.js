export default function createInterpretationLog({ props }) {
    const { message, warningCleared, priority, reviewComment } = props

    const interpretationLog = {
        message,
        warning_cleared: warningCleared,
        priority,
        review_comment: reviewComment
    }

    return { interpretationLog }
}

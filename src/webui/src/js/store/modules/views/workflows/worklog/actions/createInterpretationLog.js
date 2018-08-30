export default function createInterpretationLog({ props }) {
    const { message, warningCleared, priority } = props

    const interpretationLog = {
        message,
        warning_cleared: warningCleared,
        priority
    }

    return { interpretationLog }
}

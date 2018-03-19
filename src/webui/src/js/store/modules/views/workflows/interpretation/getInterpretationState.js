export default function getInterpretationState() {
    return {
        selected: null,
        isOngoing: false,
        dirty: false // Whether state is dirty (not saved)
    }
}

export default function getInterpretationState() {
    return {
        selected: null,
        isOngoing: false,
        dirty: false, // Whether state is dirty (not saved)
        getCurrentInterpretationData: false // Whether to load current interpretation data instead of snapshot data
    }
}

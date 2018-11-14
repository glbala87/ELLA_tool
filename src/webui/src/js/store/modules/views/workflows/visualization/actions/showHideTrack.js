export default function showHideTrack({ state, props }) {
    const { type, id, show } = props

    const tracks = state.get(`views.workflows.visualization.tracks.${type}`)
    if (tracks) {
        const trackIdx = tracks.findIndex((i) => i.id === id)
        if (trackIdx >= 0) {
            state.set(`views.workflows.visualization.tracks.${type}.${trackIdx}.selected`, show)
        }
    }
}

export default function showHideTracks({ state, props }) {
    const { tracksToUpdate } = props
    if (!tracksToUpdate || tracksToUpdate.length == 0) {
        return
    }
    const tracks = state.get(`views.workflows.visualization.tracks`)
    tracksToUpdate.forEach((trackToUpdate) => {
        const { trackId, show } = trackToUpdate
        tracks[trackId].selected = show
    })
    state.set(`views.workflows.visualization.tracks`, tracks)
}

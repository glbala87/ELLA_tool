export default function showHideTracks({ state, storage, props }) {
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
    // save selected tracks
    storage.set(
        'igvTrackSelection',
        Object.entries(tracks)
            .map(([id, cfg]) => [id, cfg.selected])
            .reduce((obj, [k, v]) => {
                obj[k] = v
                return obj
            }, {})
    )
}

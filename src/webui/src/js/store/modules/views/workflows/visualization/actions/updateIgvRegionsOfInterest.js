export default function updateIgvRegionsOfInterest({ state }) {
    const roi = state.get('views.workflows.visualization.roi')
    if (!roi) {
        return
    }
    const allRegions = Object.values(roi)
        .reduce((p, c) => {
            return p.concat(c)
        }, [])
        .filter((t) => t.selected)
        .map((t) => t.config)
    state.set(`views.workflows.visualization.igv.roi`, allRegions)
}

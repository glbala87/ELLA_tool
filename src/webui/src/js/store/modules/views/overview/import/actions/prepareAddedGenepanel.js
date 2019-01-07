export default function prepareAddedGenepanel({ state }) {
    // Copy default panel's config into addedGenepanel
    const defaultGenepanel = state.get('views.overview.import.data.defaultGenepanel')
    const addedGenepanel = {
        name: '',
        version: new Date()
            .toISOString()
            .slice(2, 10)
            .replace(/-/g, ''), // Date on format YYMMDD
        genes: {}
    }
    state.set('views.overview.import.added.addedGenepanel', addedGenepanel)
}

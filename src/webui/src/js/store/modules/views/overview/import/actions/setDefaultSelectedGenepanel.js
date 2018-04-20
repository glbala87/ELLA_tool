export default function setDefaultSelectedGenepanel({ state, props }) {
    const defaultImportGenepanel = state.get('app.user.group.default_import_genepanel')
    if (defaultImportGenepanel) {
        const genepanels = state.get('views.overview.import.data.genepanels')
        const defaultPanel = genepanels.find(gp => {
            return gp.name == defaultImportGenepanel.name &&
                   gp.version == defaultImportGenepanel.version
        })
        state.set(
            'views.overview.import.selectedGenepanel',
            defaultPanel
        )
    }
    else {
        // If no default, set first as selected
        state.set(
            'views.overview.import.selectedGenepanel',
            state.get('views.overview.import.data.genepanels.0')
        )
    }
}

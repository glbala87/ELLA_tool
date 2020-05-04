export default function checkAndSelectValidSection({ props, state, path }) {
    const sections = state.get('views.overview.sections')
    if (props.section in sections) {
        state.set('views.overview.state.selectedSection', props.section)
        return path.valid()
    }
    return path.invalid()
}

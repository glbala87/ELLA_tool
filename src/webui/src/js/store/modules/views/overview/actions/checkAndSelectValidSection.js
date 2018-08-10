export default function checkAndSelectValidSection({ props, state, path }) {
    const sections = state.get('views.overview.sections')
    if (props.section in sections) {
        state.set(`views.overview.sections.${props.section}.selected`, true)
        return path.valid()
    }
    return path.invalid()
}

export default function checkAndSelectValidSection({ props, state, path }) {
    const sectionKeys = state.get('views.overview.sectionKeys')
    const sections = state.get('views.overview.sections')
    for (const sectionKey of sectionKeys) {
        state.set(`views.overview.sections.${sectionKey}.selected`, false)
    }
    if (props.section in sections) {
        state.set(`views.overview.sections.${props.section}.selected`, true)
        return path.valid()
    }
    return path.invalid()
}

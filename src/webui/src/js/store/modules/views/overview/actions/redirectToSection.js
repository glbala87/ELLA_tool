export default function redirectToSection({ props, state, router }) {
    const section = props.section
    const sections = state.get('views.overview.sections', sections)
    const sectionKeys = state.get('views.overview.sectionKeys', sections)

    // If section is valid, redirect directly
    if (sectionKeys && section in sectionKeys) {
        router.redirect(`/overview/${section}`)
        return
    }
    // If not, check if we have previously selected section
    if (sections) {
        let selected = Object.entries(sections).find((s) => s[1].selected)
        if (selected) {
            router.redirect(`/overview/${selected[0]}`)
            return
        }
    }

    // Fallbacks
    if (sectionKeys) {
        router.redirect(`/overview/${sectionKeys[0]}`)
    }

    router.redirect(`/overview/variants`)
}

import { deepCopy } from '../../../../../util'
import { AVAILABLE_SECTIONS } from '../getOverviewState'

export default function redirectToSection({ props, state, module, router }) {
    const section = props.section
    const sections = module.get('sections', sections)
    const sectionKeys = module.get('sectionKeys', sections)

    // If section is valid, redirect directly
    if (section in sectionKeys) {
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
    router.redirect(`/overview/${sectionKeys[0]}`)
}

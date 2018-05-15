import { deepCopy } from '../../../../../util'
import { AVAILABLE_SECTIONS } from '../getOverviewState'

export default function checkAndSetValidSection({ props, state, path }) {
    const userSections = state.get('app.config.user.user_config.overview.views').slice()
    state.set('views.overview.sectionKeys', userSections)
    let sections = {}
    for (let userSection of userSections) {
        sections[userSection] = deepCopy(AVAILABLE_SECTIONS[userSection])
    }
    state.set('views.overview.sections', sections)
    if (props.section in sections) {
        state.set(`views.overview.sections.${props.section}.selected`, true)
        return path.valid()
    }
    return path.invalid()
}

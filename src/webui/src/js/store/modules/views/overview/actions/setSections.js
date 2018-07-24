import { deepCopy } from '../../../../../util'
import { AVAILABLE_SECTIONS } from '../getOverviewState'

export default function setSections({ state }) {
    const userSections = state.get('app.config.user.user_config.overview.views').slice()
    state.set('views.overview.sectionKeys', userSections)
    let sections = {}
    for (let userSection of userSections) {
        sections[userSection] = deepCopy(AVAILABLE_SECTIONS[userSection])
    }
    state.set('views.overview.sections', sections)
}

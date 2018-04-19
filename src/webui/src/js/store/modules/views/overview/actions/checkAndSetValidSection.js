import { deepCopy } from '../../../../../util'
import { AVAILABLE_SECTIONS } from '../getOverviewState'

export default function checkAndSetValidSection({ props, state, module, path, router }) {
    const userSections = state.get('app.config.user.user_config.overview.views').slice()
    module.set('sectionKeys', userSections)
    let sections = {}
    for (let userSection of userSections) {
        sections[userSection] = deepCopy(AVAILABLE_SECTIONS[userSection])
    }
    module.set('sections', sections)
    if (props.section in sections) {
        module.set(`sections.${props.section}.selected`, true)
        return path.valid()
    }
    return path.invalid()
}

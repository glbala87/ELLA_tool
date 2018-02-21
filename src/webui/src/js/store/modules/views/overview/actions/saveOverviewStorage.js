import { deepCopy } from '../../../../../util'
import { AVAILABLE_SECTIONS } from '../getOverviewState'

export default function saveOverviewStorage({ props, module }) {
    const settings = {
        selectedSection: null
    }

    const sections = module.get('sections')
    for (let [name, section] of Object.entries(sections)) {
        if (section.selected) {
            settings.selectedSection = name
        }
    }
    storage.set('overview', settings)
}

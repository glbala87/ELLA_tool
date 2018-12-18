import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'

export default Compute(state`views.overview.sections`, (sections) => {
    if (sections) {
        // [sectionName, {selected: bool}]
        return Object.entries(sections).find((s) => {
            return s[1].selected
        })[0]
    }
})

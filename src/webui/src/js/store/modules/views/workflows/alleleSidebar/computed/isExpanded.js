import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'

export default Compute(
    state`views.workflows.selectedComponent`,
    state`views.workflows.alleleSidebar.expanded`,
    (selectedComponent, expanded) => {
        if (!selectedComponent) {
            return false
        }
        return selectedComponent === 'Classification' && expanded
    }
)

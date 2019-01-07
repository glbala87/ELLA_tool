import { Compute } from 'cerebral';
import { state } from 'cerebral/tags';

export default Compute(
    state`views.workflows.interpretation.isOngoing`,
    state`views.workflows.interpretation.selected`,
    state`app.user`,
    (ongoing, interpretation, user) => {
        return !ongoing || interpretation.user.id !== user.id
    }
)

/**
 * Whether to show an exit warning or not.
 * It takes in the raw state from Cerebral,
 * as we cannot run a Compute inside a Provider.
 * Used for onBeforeUnload warning
 * @param {*} state State from Cerebral
 */
export default function showExitWarning(state) {
    console.log(state)
    return (
        state.views.workflows.interpretation.isOngoing &&
        state.views.workflows.interpretation.dirty &&
        state.app.config.app.user_confirmation_to_discard_changes
    )
}

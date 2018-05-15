export default function showModal({ state, props }) {
    state.set(`modals.${props.modalName}.show`, true)
}

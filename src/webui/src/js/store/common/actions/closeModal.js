export default function closeModal({ state, props }) {
    state.unset(`modals.${props.modalName}`)
}

export default function closeModal({ state, props }) {
    state.set(`modals.${props.modalName}.show`, false)
}

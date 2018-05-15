export default function checkSearchId({ module, props, path }) {
    if (module.get('currentSearchId') === props.currentSearchId) {
        return path.true()
    } else {
        return path.false()
    }
}

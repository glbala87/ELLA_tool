function hasInterpretations({ state, path }) {
    if (state.get('views.workflows.data.interpretations').length) {
        return path.true()
    }
    return path.false()
}

export default hasInterpretations

function progress(type, amount) {
    return ({ progress }) => {
        progress[type](amount)
    }
}

export default progress

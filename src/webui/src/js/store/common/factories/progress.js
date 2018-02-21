function progress(type, amount) {
    return function progress({ progress }) {
        progress[type](amount)
    }
}

export default progress

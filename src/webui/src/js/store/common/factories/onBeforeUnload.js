export function enableOnBeforeUnload(checkFunc, message) {
    return function enableOnBeforeUnload({ onBeforeUnload }) {
        onBeforeUnload.enable(checkFunc, message)
    }
}

export function disableOnBeforeUnload() {
    return function enableOnBeforeUnload({ onBeforeUnload }) {
        onBeforeUnload.disable()
    }
}

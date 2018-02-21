const intervals = {}
function IntervalProvider(context) {
    context.interval = {
        start(signalPath, interval, initialRun = false) {
            let signal = context.controller.getSignal(signalPath)
            intervals[signalPath] = setInterval(() => signal(), interval)
            if (initialRun) {
                signal()
            }
        },
        stop(signalPath) {
            clearInterval(intervals[signalPath])
        }
    }
    return context
}

export default IntervalProvider

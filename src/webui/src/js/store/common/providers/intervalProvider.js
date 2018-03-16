import { Provider } from 'cerebral'

const intervals = {}

function stop(signalPath) {
    if (signalPath in intervals) {
        clearInterval(intervals[signalPath])
        delete intervals[signalPath]
        return true
    }
    return false
}

export default Provider({
    start(signalPath, props, interval, initialRun = false) {
        stop(signalPath)
        let signal = this.context.controller.getSignal(signalPath)
        intervals[signalPath] = setInterval(() => signal(props), interval)
        if (initialRun) {
            signal()
        }
    },
    stop(signalPath) {
        return stop(signalPath)
    }
})

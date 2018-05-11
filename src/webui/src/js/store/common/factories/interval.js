export default function interval(funcName, ...args) {
    return function interval({ interval }) {
        interval[funcName](...args)
    }
}

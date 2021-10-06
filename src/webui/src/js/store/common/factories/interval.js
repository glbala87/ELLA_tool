export default function interval(funcName, ...args) {
    return ({ interval }) => {
        interval[funcName](...args)
    }
}

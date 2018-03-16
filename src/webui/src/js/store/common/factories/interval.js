export default function interval(funcName, ...args) {
    return function interval({ interval }) {
        console.log(args)
        interval[funcName](...args)
    }
}

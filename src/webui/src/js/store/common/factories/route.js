export function redirect(url) {
    return function redirect({ route, resolve }) {
        route.redirect(resolve.value(url))
    }
}

export function goTo(url) {
    return function goTo({ route, resolve }) {
        route(resolve.value(url))
    }
}

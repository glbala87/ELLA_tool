export default function setNavbarTitle(title) {
    return function setNavbarTitle({ state, resolve }) {
        state.set('app.navbar.title', resolve.value(title))
    }
}

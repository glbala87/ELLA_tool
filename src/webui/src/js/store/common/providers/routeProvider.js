import { Provider } from 'cerebral'
import page from 'page'

export default Provider({
    redirect(url) {
        page.redirect(url)
    },
    goTo(url) {
        page(url)
    }
})

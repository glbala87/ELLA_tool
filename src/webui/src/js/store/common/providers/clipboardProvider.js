import { Provider } from 'cerebral'
import copy from 'copy-to-clipboard'

export default Provider({
    copy() {
        copy(...arguments)
    }
})

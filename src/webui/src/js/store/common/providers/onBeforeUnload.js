import { Provider } from 'cerebral'

// onbeforeunload doesn't handle navigation on single page applications. Therefore, we intercept clicks on
// document, and checks whether the click is captured by an element that navigates away
function eventHandler(checkFunc, state, message) {
    return (event) => {
        event.stopImmediatePropagation()
        let element = event.target
        while (element && element.tagName !== 'A') {
            element = element.parentElement
        }

        if (
            element &&
            element.getAttribute('href') &&
            !element.getAttribute('target') &&
            checkFunc(state)
        ) {
            let ans = confirm(message)
            if (ans === false) {
                event.stopPropagation()
                event.preventDefault()
            } else {
                window.onbeforeunload = null
            }
        }
    }
}

export default Provider({
    enable(checkFunc, message) {
        const state = this.context.controller.getModel().state
        this.eventHandler = eventHandler(checkFunc, state, message)
        document.addEventListener('click', (event) => {
            event.stopImmediatePropagation()
            let element = event.target
            while (element && element.tagName !== 'A') {
                console.dir(element)
                element = element.parentElement
            }
            console.dir(element)

            if (
                element &&
                element.getAttribute('href') &&
                !element.getAttribute('target') &&
                checkFunc(state)
            ) {
                let ans = confirm(message)
                if (ans === false) {
                    // Stop event if confirmed
                    event.stopPropagation()
                    event.preventDefault()
                } else {
                    // If confirmed, unset onbeforeunload event handler to avoid multiple dialogue boxes
                    window.onbeforeunload = null
                }
            }
        })

        window.onbeforeunload = (event) => {
            if (checkFunc(state)) {
                event.returnValue = message
            }
        }

        window.onpopstate = (event) => {
            console.log('popstate')
            event.stopImmediatePropagation()
            event.preventDefault()
        }
    },
    disable() {
        // document is reloaded, so no need to remove event listener.
        window.onbeforeunload = null
    }
})

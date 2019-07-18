/* jshint esnext: true */

// Extracts the IIFE into an export
import wysiwyg from 'exports-loader?wysiwyg=window.wysiwyg!../../thirdparty/wysiwygjs/wysiwyg'

import { Directive, Inject } from '../ng-decorators'
import { EventListeners, UUID, sanitize } from '../util'
import template from './wysiwygEditor.ngtmpl.html'

@Directive({
    selector: 'wysiwyg-editor',
    scope: {
        placeholder: '@?',
        ngModel: '=',
        ngDisabled: '=?',
        showControls: '<?',
        templates: '=?',
        references: '=?', // [{name: 'Pending', references: [...], ...}] reference objects for quick insertion of references
        diffExisting: '=?', // Existing text for diff display mode
        diffExistingTitle: '@?' // Button title for diff display mode
    },
    require: '?ngModel', // get a hold of NgModelController
    template
})
@Inject('$scope', '$element', '$timeout', 'AttachmentResource')
export class WysiwygEditorController {
    constructor($scope, $element, $timeout, AttachmentResource) {
        this.timeout = $timeout
        this.scope = $scope
        this.element = $element[0]
        this.editorelement = $element.children()[0]
        this.diffmodeelement = $element.children()[1]
        this.placeholderelement = $element.children()[2]
        this.buttonselement = $element.children()[3]
        this.buttons = {}
        this.showControls = 'showControls' in this ? this.showControls : true

        for (const buttonElement of this.buttonselement.children) {
            let name = buttonElement.id.split('-')[1]
            this.buttons[name] = buttonElement
        }

        this.popovers = {
            linkform: {
                show: false,
                button: this.buttons['link'],
                element: this.buttonselement.children[this.buttonselement.children.length - 3]
            },
            templates: {
                show: false,
                button: this.buttons['templates'],
                element: this.buttonselement.children[this.buttonselement.children.length - 2]
            },
            references: {
                show: false,
                button: this.buttons['references'],
                element: this.buttonselement.children[this.buttonselement.children.length - 1]
            },
            fontcolor: {
                show: false,
                button: this.buttons['fontcolor'],
                element: this.buttonselement.children[this.buttonselement.children.length - 5]
            },
            highlightcolor: {
                show: false,
                button: this.buttons['highlightcolor'],
                element: this.buttonselement.children[this.buttonselement.children.length - 4]
            }
        }

        this.DEFAULT_COLOR = {
            HEX: '#F5F5F9',
            RGB: '245, 245, 249'
        }

        this.fontColors = [
            '#000000', // black
            '#FF0000', // red
            '#00B050', // green
            '#0000FF', // blue
            '#E26B0A' // orange
        ]

        this.highlightColors = [
            this.DEFAULT_COLOR.HEX,
            '#D90309', // red
            '#66FF33', // green
            '#FDFF16', // yellow
            '#0967F9' // blue
        ]

        this.attachmentResource = AttachmentResource

        this.ngModelController = $element.controller('ngModel') // Get controller for editors ngmodel

        this.buttonselement.hidden = true
        this.isBlurred = false

        this.editorMode = 'editor'
        this.diffText = ''

        this.setupEditor()
        this.setupEventListeners()

        // Watch readOnly status of editor
        this.scope.$watch('ngDisabled', () => {
            this.editor.readOnly(this.ngDisabled)
        })

        // Attach existing $viewValue to editor
        this.ngModelController.$render = () => {
            // Update view value from input should not re-render (it occasionaly does)
            // From the angular source code:
            // * The value referenced by `ng-model` is changed programmatically and both the `$modelValue` and
            // *   the `$viewValue` are different from last time.
            // This scenario can happen if cerebral is updating the $modelValue, and sets a $modelValue older than what is currently in the editor.
            // However, we do not want to let changes from cerebral trigger a re-render, as the "true" value should be editor.getHTML(), which does not
            // require a re-render.
            // This is prevented by only allowing re-rendering if the activeElement is not the editorElement.
            if (document.activeElement === this.editorelement) {
                return
            }

            if (
                typeof this.ngModelController.$viewValue === 'string' &&
                this.getTextFromHTML(this.ngModelController.$viewValue) !== ''
            ) {
                this.editor.setHTML(this.ngModelController.$viewValue)
                this.placeholderelement.hidden = true
            } else {
                this.editor.setHTML('')
                this.placeholderelement.hidden = false
            }
        }
    }

    setupEditor() {
        var options = {
            element: this.editorelement,
            onPlaceholder: (visible) => {
                this.placeholderEvent(visible)
            },
            onKeyDown: (key, character, shiftKey, altKey, ctrlKey, metaKey) => {
                if (ctrlKey || metaKey) {
                    if (character.toLowerCase() === 'b') {
                        this.editor.bold()
                        return false
                    } else if (character.toLowerCase() === 'i') {
                        this.editor.italic()
                        return false
                    } else if (character.toLowerCase() === 'u') {
                        this.editor.underline()
                        return false
                    }
                }
            },
            onSelection: (collapsed, rect, nodes, rightclick) => {
                let colors = this.getCurrentColors(nodes)
                if (colors['highlightcolors'].length === 1) {
                    this.buttons['highlightcolor'].children[1].style.color =
                        colors['highlightcolors'][0]
                } else {
                    this.buttons['highlightcolor'].children[1].style.color = `rgb(${
                        this.DEFAULT_COLOR.RGB
                    })`
                }
                if (colors['fontcolors'].length === 1) {
                    this.buttons['fontcolor'].children[0].style.color = colors['fontcolors'][0]
                } else {
                    this.buttons['fontcolor'].children[0].style.color = 'rgb(0,0,0)'
                }
            }
        }
        this.buttons['highlightcolor'].children[1].style.color = `rgb(${this.DEFAULT_COLOR.RGB})`
        this.buttons['fontcolor'].children[0].style.color = 'rgb(0,0,0)'

        this.editor = wysiwyg(options)
    }

    updateViewValue() {
        this.scope.$evalAsync(this.ngModelController.$setViewValue(this.editor.getHTML()))
        this.positionPopovers()
    }

    buttonAction(actionName) {
        const actions = {
            bold: this.editor.bold,
            italic: this.editor.italic,
            underline: this.editor.underline,
            monospace: () => this.editor.fontName('monospace'),
            orderedList: () => this.editor.insertList(true),
            unorderedList: () => this.editor.insertList(false),
            heading1: () => this.editor.format('h1'),
            heading2: () => this.editor.format('h2'),
            paragraph: () => this.editor.format('div'),
            removeFormat: () => {
                this.editor.format('div')
                this.editor.removeFormat()
            },
            linkform: () => this.togglePopover('linkform'),
            templates: () => this.togglePopover('templates'),
            references: () => this.togglePopover('references'),
            fontcolor: () => this.togglePopover('fontcolor'),
            highlightcolor: () => this.togglePopover('highlightcolor'),
            diffmode: () => this.toggleDiffMode()
        }

        actions[actionName]()
    }

    setupEventListeners() {
        let eventListeners = new EventListeners()

        // Blur whenever clicking outside. Use 'mousedown'
        // so that we don't blur when user is selecting text and
        // ending with pointer outside our element
        eventListeners.add(document, 'mousedown', (e) => {
            if (!this.editorelement.parentElement.contains(e.target)) {
                this.timeout(() => this.blur())
            }
        })

        // Update model whenever contenteditable input is triggered
        eventListeners.add(this.editorelement, 'input', (e) => {
            this.updateViewValue()
        })

        // Show ourselves when clicked upon
        eventListeners.add(this.editorelement, 'focus', () => {
            this.focus()
        })
        eventListeners.add(this.placeholderelement, 'click', () => {
            this.focus()
        })

        // Close all popovers on ESC
        eventListeners.add(document, 'keyup', (e) => {
            if (e.key === 'Escape') {
                this.timeout(() => this.closePopovers())
            }
        })

        // No need to add custom image scaling on firefox (it's already available)
        var isFirefox = typeof InstallTrigger !== 'undefined'
        if (!isFirefox) {
            eventListeners.add(this.editorelement, 'click', (e) => {
                if (!this.editor.readOnly()) {
                    this.handleImageScaling(e)
                }
            })
        }

        eventListeners.add(this.editorelement, 'paste', (e) => {
            // IMPORTANT: Use clipboardData.items rather than clipboardData.files, as this does not work for older versions of Chrome
            if (!e.clipboardData.items.length) return
            let hasAttachment = false
            if (e.clipboardData.types.indexOf('text/html') > -1) {
                let text = e.clipboardData.getData('text/html')
                e.preventDefault()
                this.editor.insertHTML(sanitize(text))
            } else {
                for (let item of e.clipboardData.items) {
                    if (item.kind !== 'file') {
                        continue
                    }
                    this.attachmentResource.post(item.getAsFile()).then((id) => {
                        let uuid = UUID()
                        let label = `Attachment ${id} ${uuid}`
                        let src = `/api/v1/attachments/${id}`
                        this.editor.insertHTML(
                            `<img id="${uuid}" src="${src}" alt="${label}" title="${label}" />`
                        )
                    })
                    hasAttachment = true
                }
                if (hasAttachment) {
                    e.preventDefault()
                }
            }
        })

        // Remove all event listeners on destroy
        this.scope.$on('$destroy', function() {
            eventListeners.removeAll()
        })
    }

    handleImageScaling(e) {
        if (e.target.tagName !== 'IMG') return

        let img = e.target
        let imgId = img.id

        let currentScale = (1.0 * img.width) / img.naturalWidth
        let minScale = 0.1
        let maxScale = 1.5

        // Create div with slider
        let sliderContainer = document.createElement('div')
        sliderContainer.classList.add('image-slider')
        let slider = document.createElement('input')
        sliderContainer.appendChild(slider)

        // Specify slider properties
        slider.type = 'range'
        slider.min = minScale
        slider.max = maxScale
        slider.step = 0.01

        const editorRect = this.editorelement.getBoundingClientRect()
        const imgRect = img.getBoundingClientRect()

        const left = imgRect.left - editorRect.left
        const top = imgRect.top - editorRect.top
        sliderContainer.style.left = left + 'px'
        sliderContainer.style.top = top + 'px'

        // Append slider to parent element
        this.editorelement.parentNode.appendChild(sliderContainer)

        slider.value = currentScale

        // Focus slider without hiding editors toolbar
        slider.focus()

        // Prevent clicking slider from affecting popovers
        slider.onclick = (e) => {
            e.stopPropagation()
        }

        slider.oninput = (e) => {
            // We have to fetch img again (for some reason)
            let imgElement = document.getElementById(imgId)

            // Scale image proportionally with slider value (height is set to auto)
            imgElement.width = slider.value * imgElement.naturalWidth
        }

        slider.onblur = (e) => {
            // Update model
            this.updateViewValue()
            // Remove slider element
            this.editorelement.parentNode.removeChild(sliderContainer)
            slider = null
            sliderContainer = null
        }
    }

    getTree(node) {
        if (!node) return []
        if (node.nodeName === 'WYSIWYG-EDITOR') {
            return [node]
        }
        return [node].concat(this.getTree(node.parentElement))
    }

    getCurrentColors(nodes) {
        let highlightcolors = []
        let fontcolors = []
        for (let i = 0; i < nodes.length; i++) {
            let subtree = this.getTree(nodes[i])
            for (let j = 0; j < subtree.length; j++) {
                if (subtree[j].style) {
                    if (subtree[j].color) {
                        fontcolors = fontcolors.concat(subtree[j].color)
                    } else {
                        fontcolors = fontcolors.concat('rgb(0,0,0)')
                    }
                    break // Check only first styled element in tree
                }
            }
            for (let j = 0; j < subtree.length; j++) {
                if (subtree[j].style && subtree[j].style['background-color']) {
                    if (subtree[j].style['background-color'] !== `rgb(${this.DEFAULT_COLOR.RGB})`) {
                        highlightcolors = highlightcolors.concat(
                            subtree[j].style['background-color']
                        )
                    } else {
                        highlightcolors = highlightcolors.concat(`rgb(${this.DEFAULT_COLOR.RGB})`) // default color
                    }
                    break // Check only first styled element in tree
                }
            }
        }
        return { fontcolors: fontcolors, highlightcolors: highlightcolors }
    }

    // Helper functions for editorelement
    placeholderEvent(visible) {
        if (document.activeElement !== this.editorelement || !visible) {
            this.placeholderelement.hidden = !visible
            this.editorelement.hidden = visible
        }
    }

    getTextFromHTML(html) {
        html = html.replace(/<\/?(br|ul|ol|strong|em|li|h1|h2|h3|h4|p|div)[^>]*>/g, '')
        html = html.replace('/s+/g', '')
        return html
    }

    blur() {
        // We cannot blur on every click, since using setHTML()
        // puts other elements in focus. Plus it's more to do on
        // every single click.
        if (!this.isBlurred) {
            this.editorMode = 'editor'
            this.closePopovers()
            this.isBlurred = true
            this.timeout(() => {
                // Set timeout so changes in layout due to removal
                // doesn't disturb what user actually clicked on
                this.buttonselement.hidden = true
            }, 100)

            // Clean up HTML
            if (!this.ngDisabled) {
                if (this.getTextFromHTML(this.editor.getHTML()) === '') {
                    this.editor.setHTML('')
                    this.placeholderEvent(true)
                }

                let html = this.editor.getHTML()
                html = html.replace(`background-color: rgb(${this.DEFAULT_COLOR.RGB});`, '')
                html = html.replace('style=""', '')
                this.editor.setHTML(html)

                // Update ngModel
                this.updateViewValue()
            }
        }
    }

    focus() {
        if (!this.editor.readOnly()) {
            this.isBlurred = false
            this.placeholderEvent(false)
            this.editorelement.focus()
            this.buttonselement.hidden = false
        }
    }

    toggleDiffMode() {
        this.editorMode = this.editorMode === 'diff' ? 'editor' : 'diff'

        if (this.editorMode === 'diff') {
            fetch('api/v1/reports/diff/', {
                headers: { 'Content-Type': 'application/json; charset=utf-8' },
                method: 'POST',
                body: JSON.stringify({
                    old: this.diffExisting,
                    new: this.editor.getHTML()
                })
            })
                .then((response) => {
                    if (!response.ok) {
                        throw Error('Something went wrong while calculating diff.')
                    }
                    return response.json()
                })
                .then((data) => {
                    this.diffmodeelement.innerHTML = data.result
                })
                .catch((err) => {
                    this.diffmodeelement.innerHTML = `<h2 style="color: red;">${err}</h2>`
                })
        } else {
            this.diffmodeelement.innerHTML = ''
        }
    }

    ////////////////
    // Popovers
    ////////////////

    togglePopover(name) {
        if (this.popovers[name].show) {
            this.closePopover(name)
        } else {
            this.openPopover(name)
        }
    }

    openPopover(name) {
        this.closePopovers()
        // Ask editor to store selection
        // it is automatically used inside execCommand
        this.editor.openPopup()
        this.popovers[name].show = true
        this.positionPopovers()
    }

    closePopover(name) {
        this.popovers[name].show = false
    }

    closePopovers() {
        for (const popoverKey of Object.keys(this.popovers)) {
            this.popovers[popoverKey].show = false
        }
    }

    positionPopovers() {
        for (const popover of Object.values(this.popovers)) {
            if (!popover.show) {
                continue
            }
            popover.element.style.left = popover.button.offsetLeft + 'px'
            popover.element.style.top =
                popover.button.offsetTop + popover.button.offsetHeight + 'px'
        }
    }

    addLink() {
        if (this.linkUrl.replace(/\s+/g, '') === '') {
            // Empty url
            this.clockPopover('linkform')
            return
        }
        if (!this.linkUrl.startsWith('http')) {
            // Should start with either http or https
            this.linkUrl = 'http://' + this.linkUrl
        }

        // Get link text
        this.linkText = this.linkText !== '' ? this.linkText : url

        // Insert link
        this.editor.insertHTML(
            '<div><a href="' +
                this.linkUrl +
                '" target="' +
                this.linkUrl +
                '"><span>' +
                this.linkText +
                '</span></a></div>'
        )
        this.linkUrl = ''
        this.linkText = ''
        this.closePopover('linkform')
    }

    insertTemplate(template) {
        this.editor.insertHTML(template.template)
        this.positionPopovers()
        this.closePopover('templates')
    }

    insertReference(ref) {
        const formatted = `${ref.authors} (${ref.year}) ${ref.journal}`
        this.editor.insertHTML(formatted)
        this.positionPopovers()
        this.closePopover('references')
    }

    formatReference(ref, withTitle) {
        if (ref) {
            if (withTitle) {
                return `${ref.authors} (${ref.year}): ${ref.title}`
            } else {
                return `${ref.authors} (${ref.year})`
            }
        }
        return ''
    }

    setFontColor(color) {
        this.editor.forecolor(color)
        this.closePopover('fontcolor')
    }

    setHighlightColor(color) {
        this.editor.highlight(color)
        this.closePopover('highlightcolor')
    }
}

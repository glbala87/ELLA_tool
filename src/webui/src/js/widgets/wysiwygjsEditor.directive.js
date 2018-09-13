/* jshint esnext: true */

// Extracts the IIFE into an export
import wysiwyg from 'exports-loader?wysiwyg=window.wysiwyg!../../thirdparty/wysiwygjs/wysiwyg'
import vanillaColorPicker from 'exports-loader?window.vanillaColorPicker!../../thirdparty/vanilla-color-picker/vanilla-color-picker.min'

import { Directive, Inject } from '../ng-decorators'
import { EventListeners, UUID } from '../util'
import template from './wysiwygEditor.ngtmpl.html'

@Directive({
    selector: 'wysiwyg-editor',
    scope: {
        placeholder: '@?',
        ngModel: '=',
        ngDisabled: '=?',
        showControls: '<?'
    },
    require: '?ngModel', // get a hold of NgModelController
    template
})
@Inject('$scope', '$element', 'AttachmentResource')
export class WysiwygEditorController {
    constructor($scope, $element, AttachmentResource) {
        this.scope = $scope
        this.element = $element[0]
        this.editorelement = $element.children()[0]
        this.placeholderelement = $element.children()[1]
        this.buttonselement = $element.children()[2]
        this.buttons = {}
        this.showControls = 'showControls' in this ? this.showControls : true
        for (let i = 0; i < this.buttonselement.children.length - 1; i++) {
            let button = this.buttonselement.children[i]
            let name = button.id.split('-')[1]
            this.buttons[name] = button
        }
        this.linkform = this.buttonselement.children[this.buttonselement.children.length - 1]

        this.attachmentResource = AttachmentResource

        this.ngModelController = $element.controller('ngModel') // Get controller for editors ngmodel

        this.buttonselement.hidden = true
        this.blurBlocked = false

        this.sourcemode = false
        this.source = ''

        this.DEFAULT_COLOR = {
            HEX: '#F5F5F9',
            RGB: '245, 245, 249'
        }

        this.setupEditor()
        this.setupEventListeners()
        this.setupColorPickers()

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
                if (colors['highlightcolors'].length == 1) {
                    this.buttons['highlightcolor'].children[1].style.color =
                        colors['highlightcolors'][0]
                } else {
                    this.buttons['highlightcolor'].children[1].style.color = `rgb(${
                        this.DEFAULT_COLOR.RGB
                    })`
                }
                if (colors['fontcolors'].length == 1) {
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
    }

    setupEventListeners() {
        let eventListeners = new EventListeners()

        // Make sure blur is not triggered on editor when a button is clicked
        for (let name in this.buttons) {
            let button = this.buttons[name]
            eventListeners.add(button, 'mousedown', () => {
                this.blurBlocked = true
            })
            if (name !== 'color' || name !== 'link') {
                eventListeners.add(button, 'mouseup', () => {
                    this.editor.openPopup()
                    this.blurBlocked = false
                })
            }
        }

        // Update model whenever contenteditable input is triggered
        eventListeners.add(this.editorelement, 'input', (e) => {
            this.updateViewValue()
        })

        // Add eventlisteners to focus and blur editorelement
        eventListeners.add(this.editorelement, 'blur', () => {
            this.blur()
        })
        eventListeners.add(this.editorelement, 'focus', () => {
            this.focus()
        })
        eventListeners.add(this.placeholderelement, 'click', () => {
            this.focus()
        })
        try {
            eventListeners.add(this.buttons['src'], 'click', () => {
                this.toggleSource()
            })
        } catch (e) {}

        // Add actions to buttons
        eventListeners.add(this.buttons['bold'], 'click', this.editor.bold)
        eventListeners.add(this.buttons['italic'], 'click', this.editor.italic)
        eventListeners.add(this.buttons['underline'], 'click', this.editor.underline)
        eventListeners.add(this.buttons['monospace'], 'click', () => {
            this.editor.fontName('monospace')
        })
        eventListeners.add(this.buttons['orderedList'], 'click', () => {
            this.editor.insertList(true)
        })
        eventListeners.add(this.buttons['unorderedList'], 'click', () => {
            this.editor.insertList(false)
        })
        eventListeners.add(this.buttons['heading1'], 'click', () => {
            this.editor.format('h1')
        })
        eventListeners.add(this.buttons['heading2'], 'click', () => {
            this.editor.format('h2')
        })
        eventListeners.add(this.buttons['paragraph'], 'click', () => {
            this.editor.format('div')
        })
        eventListeners.add(this.buttons['removeFormat'], 'click', this.editor.removeFormat)

        // Add eventhandlers on link-form
        eventListeners.add(this.buttons['link'], 'click', (e) => {
            this.handleLinkForm(e)
        })
        eventListeners.add(this.linkform, 'blur', () => {
            setTimeout(
                () => {
                    this.closeLinkForm(false, this)
                },
                1,
                false
            )
        }) // Close if active element not in link form)
        let linkinputs = this.linkform.getElementsByTagName('input')
        let addbutton = this.linkform.getElementsByTagName('button')[0]
        eventListeners.add(addbutton, 'click', () => {
            this.addLink()
        })
        for (let i = 0; i < linkinputs.length; i++) {
            eventListeners.add(linkinputs[i], 'blur', () => {
                setTimeout(
                    () => {
                        this.closeLinkForm(false, this)
                    },
                    1,
                    false
                )
            }) // Close if active element not in link form
            eventListeners.add(linkinputs[i], 'keyup', (e) => {
                this.handleLinkForm(e)
            }) // Only handles esc and enter
        }

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
            for (let item of e.clipboardData.items) {
                if (item.kind !== 'file') continue
                this.attachmentResource.post(item.getAsFile()).then((id) => {
                    let uuid = UUID()
                    let label = `Attachment ${id} ${uuid}`
                    let src = `/api/v1/attachments/${id}`
                    this.editor.insertHTML(
                        `<img id="${uuid}" src="${src}" alt="${label}" title="${label}">`
                    )
                })
                hasAttachment = true
            }
            if (hasAttachment) {
                e.preventDefault()
            }
        })

        // Remove all event listeners on destroy
        this.scope.$on('$destroy', function() {
            eventListeners.removeAll
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
        let slider = document.createElement('input')
        sliderContainer.appendChild(slider)

        // Specify slider properties
        slider.type = 'range'
        slider.min = minScale
        slider.max = maxScale
        slider.step = 0.01

        // Position slider
        sliderContainer.style.position = 'absolute'
        sliderContainer.style.zIndex = '10000000000'
        const rect = img.getBoundingClientRect()
        const left = rect.left + window.scrollX
        const top = rect.top + window.scrollY
        sliderContainer.style.left = left + 'px'
        sliderContainer.style.top = top + 'px'

        // Append slider to parent element
        const parent = document.body
        parent.appendChild(sliderContainer)

        slider.value = currentScale

        // Focus slider without hiding editors toolbar
        this.blurBlocked = true
        slider.focus()

        // Prevent clicking slider from affecting popovers
        slider.onclick = (e) => {
            e.stopPropagation()
        }

        slider.oninput = (e) => {
            // We have to fetch img again (for some reason)
            let imgElement = document.getElementById(imgId)

            // Scale image proportionally with slider value
            imgElement.width = slider.value * imgElement.naturalWidth
            imgElement.height = slider.value * imgElement.naturalHeight
        }

        slider.onblur = (e) => {
            // Allow editor to blur (will refocus if click is within editor)
            this.blurBlocked = false
            this.blur()

            // Remove slider element
            parent.removeChild(sliderContainer)
            slider = null
            sliderContainer = null
        }
    }

    setupColorPickers() {
        // Add font color picker
        let fontcolors = [
            '#000000', // black
            '#FF0000', // red
            '#00B050', // green
            '#0000FF', // blue
            '#E26B0A' // orange
        ]

        let fontpicker = vanillaColorPicker(this.buttons['fontcolor'])
        fontpicker.set('customColors', fontcolors)
        fontpicker.on('pickerClosed', () => {
            this.editor.closePopup()
            this.blurBlocked = false
        })
        fontpicker.on('colorChosen', (color) => {
            this.editor.closePopup()
            this.editor.forecolor(color)
            this.editor.openPopup()
        })

        // Add highlight color picker
        let highlightcolors = [
            this.DEFAULT_COLOR.HEX,
            '#D90309', // red
            '#66FF33', // green
            '#FDFF16', // yellow
            '#0967F9' // blue
        ]

        let highlightpicker = vanillaColorPicker(this.buttons['highlightcolor'])
        highlightpicker.set('customColors', highlightcolors)
        highlightpicker.on('pickerClosed', () => {
            this.editor.closePopup()
            this.blurBlocked = false
        })
        highlightpicker.on('colorChosen', (color) => {
            this.editor.closePopup()
            this.editor.highlight(color)
            this.editor.openPopup()
        })
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
        if (!this.blurBlocked) {
            if (this.getTextFromHTML(this.editor.getHTML()) === '') {
                this.editor.setHTML('')
                this.placeholderEvent(true)
            }

            // Clean up html highlight color with no effect
            let html = this.editor.getHTML()
            html = html.replace(`background-color: rgb(${this.DEFAULT_COLOR.RGB});`, '')
            html = html.replace('style=""', '')
            this.editor.setHTML(html)
            this.closeLinkForm(true)
            this.buttonselement.hidden = true

            // Update ngModel
            this.updateViewValue()
        }
    }

    focus() {
        if (!this.editor.readOnly()) {
            this.placeholderEvent(false)
            this.editorelement.focus()
            this.buttonselement.hidden = false
        }
    }

    addLink() {
        // Get url
        let url = this.linkform.children[0].children[0].value

        if (url.replace(/\s+/g, '') === '') {
            // Empty url
            this.closeLinkForm(true)
            return
        }
        if (!url.startsWith('http')) {
            // Should start with either http or https
            url = 'http://' + url
        }

        // Get link text
        let linktext = this.linkform.children[1].children[0].value
        linktext = linktext !== '' ? linktext : url

        // Insert link
        this.editor.insertHTML(
            '<div><a href="' +
                url +
                '" target="' +
                url +
                '"><span>' +
                linktext +
                '</span></a></div>'
        )
        this.closeLinkForm(true)
    }

    closeLinkForm(force, thisObj) {
        // As this function is occasionally called from a setTimeout, this will sometimes point to the global window object
        // To circumvent this, we pass in this as thisObj in those cases
        if (!thisObj) thisObj = this

        if (!force && thisObj.linkform.includes(document.activeElement)) {
            // Link form is still active
            return
        }
        thisObj.linkform.hidden = true

        // Clear inputs
        let inputs = thisObj.linkform.getElementsByTagName('input')
        for (let i = 0; i < inputs.length; i++) {
            inputs[i].value = ''
        }

        thisObj.editor.closePopup().collapseSelection()
        thisObj.blurBlocked = false
    }

    // Handle link form
    handleLinkForm(e) {
        let src = e.target || e.srcElement

        if (
            src.nodeName !== 'INPUT' &&
            (src === this.buttons['link'] || this.buttons['link'].includes(src))
        ) {
            // Open or close link form
            if (this.linkform.hidden) {
                this.editor.openPopup() // Save selection, to later add link at right location
                // Compute position
                let top = this.buttons['link'].offsetTop
                let height = this.buttons['link'].offsetHeight
                let left = this.buttons['link'].offsetLeft
                this.linkform.style.left = left + 'px'
                this.linkform.style.top = top + height + 'px'

                this.linkform.hidden = false
            } else {
                this.closeLinkForm(true)
            }
        } else if (src.nodeName === 'INPUT') {
            if (typeof e.type === 'click') {
                src.focus()
            } else if (e.type === 'keyup') {
                if (e.key === 'Escape') {
                    this.closeLinkForm(true)
                } else if (e.key === 'Enter') {
                    this.addLink()
                }
            }
        }
    }

    toggleSource() {
        if (this.sourcemode) {
            this.editor.setHTML(this.source)
        } else {
            this.source = this.editor.getHTML()
            this.editor.setHTML(this.source.replace(/</g, '&lt;').replace(/>/g, '&gt;'))
        }
        this.editor.readOnly(!this.sourcemode)
        this.sourcemode = !this.sourcemode
        for (let btn in this.buttons) {
            if (btn !== 'src') {
                this.buttons[btn].disabled = this.editor.readOnly()
            }
        }
    }
}

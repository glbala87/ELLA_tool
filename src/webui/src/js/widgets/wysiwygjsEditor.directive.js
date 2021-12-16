/* jshint esnext: true */

// Extracts the IIFE into an export
import wysiwyg from 'exports-loader?wysiwyg=window.wysiwyg!../../thirdparty/wysiwygjs/wysiwyg'

// import { Directive, Inject } from '../ng-decorators'
import { EventListeners, UUID, sanitize } from '../util'
import template from './wysiwygEditor.ngtmpl.html' // eslint-disable-line no-unused-vars
import { connect } from '@cerebral/angularjs'
import app from '../ng-decorators'
import { state, signal } from 'cerebral/tags'

// import fileUpload from '@cerebral/http/lib/fileUpload'
// console.log(fileUpload)
app.component('wysiwygEditor', {
    templateUrl: 'wysiwygEditor.ngtmpl.html',
    bindings: {
        placeholder: '@?',
        ngModel: '=',
        ngDisabled: '<?',
        showControls: '<?',
        templates: '=?',
        references: '=?', // [{name: 'Pending', references: [...], ...}] reference objects for quick insertion of references
        collapsed: '=?',
        expandFn: '&'
    },
    require: '?ngModel', // get a hold of NgModelController
    controller: connect(
        {
            username: state`app.user.username`,
            postAttachment: signal`views.workflows.interpretation.postAttachment`
        },
        'WysiwygEditor',
        [
            '$scope',
            '$element',
            '$timeout',
            'cerebral',
            ($scope, $element, $timeout, cerebral) => {
                const $ctrl = $scope.$ctrl

                // Get the helper function for uploading files
                const uploadFile = cerebral.controller.contextProviders.http.definition.uploadFile

                Object.assign($ctrl, {
                    init: () => {
                        $ctrl.editorelement = $element.children()[0]
                        $ctrl.previewelement = $element.children()[1]
                        $ctrl.placeholderelement = $element.children()[2]
                        $ctrl.buttonselement = $element.children()[3]
                        $ctrl.editorelement.hidden = $ctrl.collapsed
                        $ctrl.previewelement.hidden = !$ctrl.collapsed

                        $ctrl.buttons = {}
                        $ctrl.showControls = 'showControls' in $ctrl ? $ctrl.showControls : true

                        for (const buttonElement of $ctrl.buttonselement.children) {
                            let name = buttonElement.id.split('-')[1]
                            $ctrl.buttons[name] = buttonElement
                        }

                        // Popovers for certain control buttons
                        $ctrl.popovers = {
                            linkform: {
                                show: false,
                                button: $ctrl.buttons['link'],
                                element:
                                    $ctrl.buttonselement.children[
                                        $ctrl.buttonselement.children.length - 3
                                    ]
                            },
                            templates: {
                                show: false,
                                button: $ctrl.buttons['templates'],
                                element:
                                    $ctrl.buttonselement.children[
                                        $ctrl.buttonselement.children.length - 2
                                    ]
                            },
                            references: {
                                show: false,
                                button: $ctrl.buttons['references'],
                                element:
                                    $ctrl.buttonselement.children[
                                        $ctrl.buttonselement.children.length - 1
                                    ]
                            },
                            fontcolor: {
                                show: false,
                                button: $ctrl.buttons['fontcolor'],
                                element:
                                    $ctrl.buttonselement.children[
                                        $ctrl.buttonselement.children.length - 5
                                    ]
                            },
                            highlightcolor: {
                                show: false,
                                button: $ctrl.buttons['highlightcolor'],
                                element:
                                    $ctrl.buttonselement.children[
                                        $ctrl.buttonselement.children.length - 4
                                    ]
                            }
                        }

                        $ctrl.DEFAULT_COLOR = {
                            HEX: '#F5F5F9',
                            RGB: '245, 245, 249'
                        }

                        $ctrl.fontColors = [
                            '#000000', // black
                            '#FF0000', // red
                            '#00B050', // green
                            '#0000FF', // blue
                            '#E26B0A' // orange
                        ]

                        $ctrl.highlightColors = [
                            $ctrl.DEFAULT_COLOR.HEX,
                            '#D90309', // red
                            '#66FF33', // green
                            '#FDFF16', // yellow
                            '#0967F9' // blue
                        ]

                        // $ctrl.attachmentResource = AttachmentResource

                        $ctrl.ngModelController = $element.controller('ngModel') // Get controller for editors ngmodel

                        // Add positive debounce to avoid javascript error deep in AngularJS on 'blur'
                        $ctrl.ngModelController.$overrideModelOptions({ debounce: 1 })

                        $ctrl.buttonselement.hidden = true
                        $ctrl.isBlurred = true

                        $ctrl.sourcemode = false
                        $ctrl.source = ''

                        $ctrl.setupEditor()
                        $ctrl.setupEventListeners()

                        $scope.$watch(
                            () => {
                                return $ctrl.collapsed
                            },
                            () => {
                                const hasPlaceholder = !$ctrl.placeholderelement.hidden
                                $ctrl.editorelement.hidden = hasPlaceholder || $ctrl.collapsed
                                $ctrl.previewelement.hidden = hasPlaceholder || !$ctrl.collapsed
                                $ctrl.updatePreview()
                            }
                        )

                        // Watch readOnly status of editor
                        $scope.$watch(
                            () => {
                                return $ctrl.ngDisabled
                            },
                            () => {
                                $ctrl.editor.readOnly($ctrl.ngDisabled)
                            }
                        )

                        // Attach existing $viewValue to editor
                        $ctrl.ngModelController.$render = () => {
                            // Update view value from input should not re-render (it occasionaly does)
                            // From the angular source code:
                            // * The value referenced by `ng-model` is changed programmatically and both the `$modelValue` and
                            // *   the `$viewValue` are different from last time.
                            // This scenario can happen if cerebral is updating the $modelValue, and sets a $modelValue older than what is currently in the editor.
                            // However, we do not want to let changes from cerebral trigger a re-render, as the "true" value should be editor.getHTML(), which does not
                            // require a re-render.
                            // This is prevented by only allowing re-rendering if the activeElement is not the editorElement.
                            if (document.activeElement === $ctrl.editorelement) {
                                return
                            }

                            if (
                                typeof $ctrl.ngModelController.$viewValue === 'string' &&
                                $ctrl.getTextFromHTML($ctrl.ngModelController.$viewValue) !== ''
                            ) {
                                $ctrl.editor.setHTML($ctrl.ngModelController.$viewValue)
                                $ctrl.placeholderEvent(false)
                            } else {
                                $ctrl.editor.setHTML('')
                                $ctrl.placeholderEvent(true)
                            }
                        }
                    },
                    /**
                     * Creates the wysiwygjs editor on $ctrl.editorelement
                     */
                    setupEditor: () => {
                        var options = {
                            element: $ctrl.editorelement,
                            onPlaceholder: (visible) => {
                                $ctrl.placeholderEvent(visible)
                            },
                            onKeyDown: (key, character, shiftKey, altKey, ctrlKey, metaKey) => {
                                // "s" key
                                if (altKey && key == 83) {
                                    $ctrl.insertSignature()
                                    return false
                                }
                                if (ctrlKey || metaKey) {
                                    if (character.toLowerCase() === 'b') {
                                        $ctrl.editor.bold()
                                        return false
                                    } else if (character.toLowerCase() === 'i') {
                                        $ctrl.editor.italic()
                                        return false
                                    } else if (character.toLowerCase() === 'u') {
                                        $ctrl.editor.underline()
                                        return false
                                    }
                                }
                            },
                            onSelection: (collapsed, rect, nodes, rightclick) => {
                                // Show color of selected text in highlight/font color buttons
                                const getCurrentColors = (nodes) => {
                                    const getTree = (node) => {
                                        if (!node) return []
                                        if (node.nodeName === 'WYSIWYG-EDITOR') {
                                            return [node]
                                        }
                                        return [node].concat(getTree(node.parentElement))
                                    }
                                    let highlightcolors = []
                                    let fontcolors = []
                                    for (let i = 0; i < nodes.length; i++) {
                                        let subtree = getTree(nodes[i])
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
                                            if (
                                                subtree[j].style &&
                                                subtree[j].style['background-color']
                                            ) {
                                                if (
                                                    subtree[j].style['background-color'] !==
                                                    `rgb(${$ctrl.DEFAULT_COLOR.RGB})`
                                                ) {
                                                    highlightcolors = highlightcolors.concat(
                                                        subtree[j].style['background-color']
                                                    )
                                                } else {
                                                    highlightcolors = highlightcolors.concat(
                                                        `rgb(${$ctrl.DEFAULT_COLOR.RGB})`
                                                    ) // default color
                                                }
                                                break // Check only first styled element in tree
                                            }
                                        }
                                    }
                                    return {
                                        fontcolors: fontcolors,
                                        highlightcolors: highlightcolors
                                    }
                                }

                                let colors = getCurrentColors(nodes)

                                if (colors['highlightcolors'].length === 1) {
                                    $ctrl.buttons['highlightcolor'].children[1].style.color =
                                        colors['highlightcolors'][0]
                                } else {
                                    $ctrl.buttons[
                                        'highlightcolor'
                                    ].children[1].style.color = `rgb(${$ctrl.DEFAULT_COLOR.RGB})`
                                }
                                if (colors['fontcolors'].length === 1) {
                                    $ctrl.buttons['fontcolor'].children[0].style.color =
                                        colors['fontcolors'][0]
                                } else {
                                    $ctrl.buttons['fontcolor'].children[0].style.color =
                                        'rgb(0,0,0)'
                                }
                            }
                        }
                        $ctrl.buttons[
                            'highlightcolor'
                        ].children[1].style.color = `rgb(${$ctrl.DEFAULT_COLOR.RGB})`
                        $ctrl.buttons['fontcolor'].children[0].style.color = 'rgb(0,0,0)'

                        $ctrl.editor = wysiwyg(options)
                    },
                    updateViewValue: () => {
                        let s = $ctrl.editor.getHTML()
                        s = s == '<br>' ? '' : s // fix empty editor returning <br>
                        $scope.$evalAsync($ctrl.ngModelController.$setViewValue(s))
                        $ctrl.positionPopovers()
                    },
                    /**
                     * Returns function responsible for handling the action triggered by clicking a
                     * toolbar button
                     *
                     * @param {String} actionName Name of action to get function for
                     */
                    buttonAction: (actionName) => {
                        const actions = {
                            bold: $ctrl.editor.bold,
                            italic: $ctrl.editor.italic,
                            underline: $ctrl.editor.underline,
                            monospace: () => $ctrl.editor.fontName('monospace'),
                            orderedList: () => $ctrl.editor.insertList(true),
                            unorderedList: () => $ctrl.editor.insertList(false),
                            heading1: () => $ctrl.editor.format('h1'),
                            heading2: () => $ctrl.editor.format('h2'),
                            paragraph: () => $ctrl.editor.format('div'),
                            removeFormat: () => {
                                $ctrl.editor.format('div')
                                $ctrl.editor.removeFormat()
                            },
                            linkform: () => $ctrl.togglePopover('linkform'),
                            templates: () => $ctrl.togglePopover('templates'),
                            references: () => $ctrl.togglePopover('references'),
                            fontcolor: () => $ctrl.togglePopover('fontcolor'),
                            highlightcolor: () => $ctrl.togglePopover('highlightcolor'),
                            src: () => $ctrl.toggleSource,
                            signature: () => $ctrl.insertSignature()
                        }

                        actions[actionName]()
                    },

                    /**
                     * Create event listeners on the editor, e.g. focus, blur, update and paste
                     */
                    setupEventListeners: () => {
                        let eventListeners = new EventListeners()

                        // Blur whenever clicking outside. Use 'mousedown'
                        // so that we don't blur when user is selecting text and
                        // ending with pointer outside our element
                        eventListeners.add(document, 'mousedown', (e) => {
                            if (!$ctrl.editorelement.parentElement.contains(e.target)) {
                                $timeout(() => $ctrl.blur())
                            }
                        })

                        // Update model whenever contenteditable input is triggered
                        eventListeners.add($ctrl.editorelement, 'input', (e) => {
                            $ctrl.updateViewValue()
                        })

                        // Show ourselves when clicked upon
                        eventListeners.add($ctrl.editorelement, 'focus', () => {
                            $ctrl.focus()
                        })
                        eventListeners.add($ctrl.placeholderelement, 'click', () => {
                            $ctrl.focus()
                        })

                        eventListeners.add($ctrl.previewelement, 'click', () => {
                            $ctrl.focus()
                        })

                        // Close all popovers on ESC
                        eventListeners.add(document, 'keyup', (e) => {
                            if (e.key === 'Escape') {
                                $timeout(() => $ctrl.closePopovers())
                            }
                        })

                        // Add slider to scale image
                        // No need to add custom image scaling on firefox (it's already available)
                        var isFirefox = typeof InstallTrigger !== 'undefined'
                        if (!isFirefox) {
                            eventListeners.add($ctrl.editorelement, 'click', (e) => {
                                if (!$ctrl.editor.readOnly()) {
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

                                    const editorRect = $ctrl.editorelement.getBoundingClientRect()
                                    const imgRect = img.getBoundingClientRect()

                                    const left = imgRect.left - editorRect.left
                                    const top = imgRect.top - editorRect.top
                                    sliderContainer.style.left = left + 'px'
                                    sliderContainer.style.top = top + 'px'

                                    // Append slider to parent element
                                    $ctrl.editorelement.parentNode.appendChild(sliderContainer)

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
                                        $ctrl.updateViewValue()
                                        // Remove slider element
                                        $ctrl.editorelement.parentNode.removeChild(sliderContainer)
                                        slider = null
                                        sliderContainer = null
                                    }
                                }
                            })
                        }

                        eventListeners.add($ctrl.editorelement, 'paste', (e) => {
                            // IMPORTANT: Use clipboardData.items rather than clipboardData.files, as this does not work for older versions of Chrome
                            if (!e.clipboardData.items.length) return
                            let hasAttachment = false
                            if (e.clipboardData.types.indexOf('text/html') > -1) {
                                let text = e.clipboardData.getData('text/html')
                                e.preventDefault()
                                $ctrl.editor.insertHTML(sanitize(text))
                            } else {
                                hasAttachment = true
                                e.preventDefault()
                                for (let item of e.clipboardData.items) {
                                    if (item.kind !== 'file') {
                                        continue
                                    }

                                    // Ideally we'd want to do this with a signal, but we can not return anything from a signal
                                    // without putting it in state. Therefore, we take the shortcut and use Cerebral's http
                                    // provider directly here to update the content in the editor with link to the uploaded image
                                    uploadFile('attachments/upload/', item.getAsFile(), {
                                        name: 'file'
                                    }).then((response) => {
                                        const id = response.result.id
                                        let uuid = UUID()
                                        let label = `Attachment ${id} ${uuid}`
                                        let src = `/api/v1/attachments/${id}`
                                        $ctrl.editor.insertHTML(
                                            `<img id="${uuid}" src="${src}" alt="${label}" title="${label}">`
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
                        $scope.$on('$destroy', function() {
                            eventListeners.removeAll()
                        })
                    },

                    // Helper functions for editorelement
                    placeholderEvent: (showPlaceholder) => {
                        console.log($ctrl.placeholder, showPlaceholder)
                        if (document.activeElement !== $ctrl.editorelement || !showPlaceholder) {
                            $ctrl.placeholderelement.hidden = !showPlaceholder
                            $ctrl.editorelement.hidden = $ctrl.collapsed || showPlaceholder
                            $ctrl.previewelement.hidden = !$ctrl.collapsed || showPlaceholder

                            if (showPlaceholder) {
                                // Placeholder updates can trigger for certain changes to the editor content
                                // outside the normal flow. If wysiwyg module tells us to show placeholder,
                                // something might have cleared the content outside AngularJS digest.
                                // If so, we should update our model and UI state accordingly.
                                $ctrl.blur()
                            }
                        }
                    },

                    getTextFromHTML: (html) => {
                        // Ignore all elements (except <img>)
                        html = html.replace(/<(?!\s*img)[^>]*>/g, '')
                        // Ignore inline comments
                        html = html.replace(/<!--[\s\S]*-->/g, '')
                        // Ignore all whitespace
                        html = html.replace(/s+/g, '')
                        return html
                    },

                    updatePreview: () => {
                        const parser = new DOMParser()
                        const editorHtml = parser.parseFromString(
                            $ctrl.ngModelController.$viewValue,
                            'text/html'
                        )
                        const eBody0 = editorHtml.getElementsByTagName('body')[0]
                        $ctrl.previewelement.innerText = eBody0.innerText
                        const maxChar = 135
                        const ellipsis = '...'
                        $ctrl.previewelement.innerText =
                            $ctrl.previewelement.innerText.length <= maxChar
                                ? $ctrl.previewelement.innerText
                                : $ctrl.previewelement.innerText.substring(0, maxChar) +
                                  ` ${ellipsis}`
                        // force-show ellipsis if the orgiginal innerHTML was not empty
                        if (
                            $ctrl.previewelement.innerText.trim() === '' &&
                            eBody0.innerHTML !== ''
                        ) {
                            $ctrl.previewelement.innerText = ellipsis
                        }
                    },

                    blur: () => {
                        // We cannot blur on every click, since using setHTML()
                        // puts other elements in focus. Plus it's more to do on
                        // every single click.
                        if (!$ctrl.isBlurred) {
                            $ctrl.closePopovers()
                            $ctrl.isBlurred = true
                            $timeout(() => {
                                // Set timeout so changes in layout due to removal
                                // doesn't disturb what user actually clicked on
                                $ctrl.buttonselement.hidden = true
                            }, 100)

                            // Clean up HTML
                            if (!$ctrl.ngDisabled) {
                                if ($ctrl.getTextFromHTML($ctrl.editor.getHTML()) === '') {
                                    $ctrl.editor.setHTML('')
                                    $ctrl.placeholderEvent(true)
                                }

                                let html = $ctrl.editor.getHTML()
                                html = html.replace(
                                    `background-color: rgb(${$ctrl.DEFAULT_COLOR.RGB});`,
                                    ''
                                )
                                html = html.replace('style=""', '')
                                $ctrl.editor.setHTML(html)

                                // Update ngModel
                                $ctrl.updateViewValue()
                            }
                        }
                    },

                    focus: () => {
                        if (!$ctrl.editor.readOnly()) {
                            if ($ctrl.collapsed !== undefined && $ctrl.collapsed) {
                                $ctrl.expandFn({ collapsed: false })
                            }

                            $ctrl.isBlurred = false
                            $ctrl.placeholderEvent(false)
                            $ctrl.editorelement.focus()
                            $ctrl.buttonselement.hidden = false
                        }
                    },

                    /**
                     * Debug function to show html source
                     */
                    toggleSource: () => {
                        if ($ctrl.sourcemode) {
                            $ctrl.editor.setHTML($ctrl.source)
                        } else {
                            $ctrl.source = $ctrl.editor.getHTML()
                            $ctrl.editor.setHTML(
                                $ctrl.source.replace(/</g, '&lt;').replace(/>/g, '&gt;')
                            )
                        }
                        $ctrl.editor.readOnly(!$ctrl.sourcemode)
                        $ctrl.sourcemode = !$ctrl.sourcemode
                        for (let btn in $ctrl.buttons) {
                            if (btn !== 'src') {
                                $ctrl.buttons[btn].disabled = $ctrl.editor.readOnly()
                            }
                        }
                    },

                    ////////////////
                    // Popovers
                    ////////////////

                    togglePopover: (name) => {
                        if ($ctrl.popovers[name].show) {
                            // Popover is visible, close it
                            $ctrl.closePopover(name)
                        } else {
                            // Popover is closed, open it
                            $ctrl.openPopover(name)
                        }
                    },

                    openPopover: (name) => {
                        $ctrl.closePopovers()
                        // Ask editor to store selection
                        // it is automatically used inside execCommand
                        $ctrl.editor.openPopup()
                        $ctrl.popovers[name].show = true
                        $ctrl.positionPopovers()
                    },

                    closePopover: (name) => {
                        $ctrl.popovers[name].show = false
                    },

                    closePopovers: () => {
                        for (const popoverKey of Object.keys($ctrl.popovers)) {
                            $ctrl.popovers[popoverKey].show = false
                        }
                    },

                    positionPopovers: () => {
                        for (const popover of Object.values($ctrl.popovers)) {
                            if (!popover.show) {
                                continue
                            }
                            popover.element.style.left = popover.button.offsetLeft + 'px'
                            popover.element.style.top =
                                popover.button.offsetTop + popover.button.offsetHeight + 'px'
                        }
                    },

                    addLink: () => {
                        if ($ctrl.linkUrl.replace(/\s+/g, '') === '') {
                            // Empty url
                            $ctrl.closePopover('linkform')
                            return
                        }
                        if (!$ctrl.linkUrl.startsWith('http')) {
                            // Should start with either http or https
                            $ctrl.linkUrl = 'http://' + $ctrl.linkUrl
                        }

                        // Get link text
                        $ctrl.linkText = $ctrl.linkText !== '' ? $ctrl.linkText : url

                        // Insert link
                        $ctrl.editor.insertHTML(
                            '<div><a href="' +
                                $ctrl.linkUrl +
                                '" target="' +
                                $ctrl.linkUrl +
                                '"><span>' +
                                $ctrl.linkText +
                                '</span></a></div>'
                        )
                        $ctrl.linkUrl = ''
                        $ctrl.linkText = ''
                        $ctrl.closePopover('linkform')
                    },

                    insertTemplate: (template) => {
                        $ctrl.editor.insertHTML(template.template)
                        $ctrl.positionPopovers()
                        $ctrl.closePopover('templates')
                    },

                    insertSignature: () => {
                        const d = new Date().toISOString().substring(0, 10)
                        $ctrl.editor.insertHTML(
                            `[<font color="#0000ff">${$ctrl.username}, ${d}</font>]`
                        )
                    },

                    insertReference: (ref) => {
                        const formatted = `${ref.authors} (${ref.year}) ${ref.journal}`
                        $ctrl.editor.insertHTML(formatted)
                        $ctrl.positionPopovers()
                        $ctrl.closePopover('references')
                    },

                    formatReference: (ref, withTitle) => {
                        if (ref) {
                            if (withTitle) {
                                return `${ref.authors} (${ref.year}): ${ref.title}`
                            } else {
                                return `${ref.authors} (${ref.year})`
                            }
                        }
                        return ''
                    },

                    setFontColor: (color) => {
                        $ctrl.editor.forecolor(color)
                        $ctrl.closePopover('fontcolor')
                    },

                    setHighlightColor: (color) => {
                        $ctrl.editor.highlight(color)
                        $ctrl.closePopover('highlightcolor')
                    }
                })

                // Set up editor
                $ctrl.init()
            }
        ]
    )
})

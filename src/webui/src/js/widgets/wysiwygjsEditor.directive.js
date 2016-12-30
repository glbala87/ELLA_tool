/* jshint esnext: true */

import {Directive, Inject} from '../ng-decorators';


/** Class to contain eventlisteners, so they can be detached using removeAll */
class EventListeners {
    constructor() {
        this.eventListeners = [];
    }

    add(el, type, func) {
        el.addEventListener(type, func);
        this.eventListeners.push({"element": el, "type": type, "function": func});
    }

    remove(el, type, func) {
        el.removeEventListener(type, func);
    }

    removeAll() {
        for (let i=0; i<this.eventListeners.length; i++) {
            let el = this.eventListeners[i];
            this.remove(el.element, el.type, el.function);
        }
    }
}

function addColorPicker(el) {
    var picker = vanillaColorPicker(el);
    console.log(picker);
    document.execCommand('styleWithCSS', false, true);
    picker.set('customColors', [
        'rgba(0,0,0,0.95)', // black
        'rgba(129,62,49,0.95)', // red
        'rgba(49,96,129,0.95)', // blue
        'rgba(49,129,123,0.95)', // green
        'rgba(155,135,75,0.95)', // yellow
        'rgba(49,56,129,0.95)', // purple
        'rgba(96,49,129,0.95)' // pink
    ]);
    return picker;
}

function getTree(node) {
    if (node.nodeName === "WYSIWYG-EDITOR") {
        return [node];
    }
    return [node].concat(getTree(node.parentElement))
}


function isInsideTable(nodes) {
    for (let i=0; i<nodes.length; i++) {
        let subtree = getTree(nodes[i]);
        for (let j=0; j<subtree.length; j++) {
            if (subtree[j].nodeName === "TABLE") {
                return true;
            }
        }
    }
    return false;
}

function getCurrentColors(nodes) {
    let colors = [];
    for (let i=0; i<nodes.length; i++) {
        let subtree = getTree(nodes[i]);
        for (let j=0; j<subtree.length; j++) {
            if (subtree[j].style) {
                if (subtree[j].style.color) {
                    colors = colors.concat(subtree[j].style.color)
                } else {
                    colors = colors.concat('rgba(0,0,0,0.95)') // default color
                }
                break;
            }
        }
    }

    return colors;
}



@Directive({
    selector: 'wysiwyg-editor',
    scope: {
        placeholder: '@?',
        ngModel: '=',
        ngDisabled: '=?'
    },
    require: '?ngModel', // get a hold of NgModelController
    template: '<div class="wysiwygeditor" spellcheck="false" ng-disabled="vm.ngDisabled" ng-model="comment.model.comment"></div>' +
              '<div class="wysiwygplaceholder"></div> ' +
              '<div class="wysiwygbuttons">' +
                '<button class="wysiwygbutton" id="wysiwyg-src">&lt;&gt;</button>' +
                '<button class="wysiwygbutton" title="Bold (Ctrl+B)" style="font-weight: bold" id="wysiwyg-bold">B</button>' +
                '<button class="wysiwygbutton" title="Italic (Ctrl+I)" id="wysiwyg-italic">I</button>' +
                '<button class="wysiwygbutton" title="Underline (Ctrl+U)" id="wysiwyg-underline">U</button>' +
                '<button class="wysiwygbutton" title="Heading 1" id="wysiwyg-heading1">H1</button>' +
                '<button class="wysiwygbutton" title="Heading 2" id="wysiwyg-heading2">H2</button>' +
                '<button class="wysiwygbutton" title="Normal text" id="wysiwyg-paragraph">P</button>' +
                '<button class="wysiwygbutton" title="Bullet list" id="wysiwyg-orderedList"><svg width="60%" height="100%" fill="currentcolor" stroke="currentcolor" viewBox="0 0 1792 1792" xmlns="http://www.w3.org/2000/svg"><path d="M381 1620q0 80-54.5 126t-135.5 46q-106 0-172-66l57-88q49 45 106 45 29 0 50.5-14.5t21.5-42.5q0-64-105-56l-26-56q8-10 32.5-43.5t42.5-54 37-38.5v-1q-16 0-48.5 1t-48.5 1v53h-106v-152h333v88l-95 115q51 12 81 49t30 88zm2-627v159h-362q-6-36-6-54 0-51 23.5-93t56.5-68 66-47.5 56.5-43.5 23.5-45q0-25-14.5-38.5t-39.5-13.5q-46 0-81 58l-85-59q24-51 71.5-79.5t105.5-28.5q73 0 123 41.5t50 112.5q0 50-34 91.5t-75 64.5-75.5 50.5-35.5 52.5h127v-60h105zm1409 319v192q0 13-9.5 22.5t-22.5 9.5h-1216q-13 0-22.5-9.5t-9.5-22.5v-192q0-14 9-23t23-9h1216q13 0 22.5 9.5t9.5 22.5zm-1408-899v99h-335v-99h107q0-41 .5-122t.5-121v-12h-2q-8 17-50 54l-71-76 136-127h106v404h108zm1408 387v192q0 13-9.5 22.5t-22.5 9.5h-1216q-13 0-22.5-9.5t-9.5-22.5v-192q0-14 9-23t23-9h1216q13 0 22.5 9.5t9.5 22.5zm0-512v192q0 13-9.5 22.5t-22.5 9.5h-1216q-13 0-22.5-9.5t-9.5-22.5v-192q0-13 9.5-22.5t22.5-9.5h1216q13 0 22.5 9.5t9.5 22.5z"/></svg></button> ' +
                '<button class="wysiwygbutton" title="Numbered list" id="wysiwyg-unorderedList"><svg width="60%" height="100%" fill="currentcolor" stroke="currentcolor" viewBox="0 0 1792 1792" xmlns="http://www.w3.org/2000/svg"><path class="path1" d="M384 1408q0 80-56 136t-136 56-136-56-56-136 56-136 136-56 136 56 56 136zm0-512q0 80-56 136t-136 56-136-56-56-136 56-136 136-56 136 56 56 136zm1408 416v192q0 13-9.5 22.5t-22.5 9.5h-1216q-13 0-22.5-9.5t-9.5-22.5v-192q0-13 9.5-22.5t22.5-9.5h1216q13 0 22.5 9.5t9.5 22.5zm-1408-928q0 80-56 136t-136 56-136-56-56-136 56-136 136-56 136 56 56 136zm1408 416v192q0 13-9.5 22.5t-22.5 9.5h-1216q-13 0-22.5-9.5t-9.5-22.5v-192q0-13 9.5-22.5t22.5-9.5h1216q13 0 22.5 9.5t9.5 22.5zm0-512v192q0 13-9.5 22.5t-22.5 9.5h-1216q-13 0-22.5-9.5t-9.5-22.5v-192q0-13 9.5-22.5t22.5-9.5h1216q13 0 22.5 9.5t9.5 22.5z"></path></svg></button>' +
                '<button class="wysiwygbutton" title="Clear formatting" id="wysiwyg-removeFormat">T<span style="vertical-align: sub; margin-left: -0.3rem">&#10005</span></button>' +
                '<button class="wysiwygbutton" title="Set text color" id="wysiwyg-color">A<span style="color: rgba(0,0,0,0.95); vertical-align: sub; margin-left: -0.0rem">&#9646</span></button>' +
                '<button class="wysiwygbutton" title="Add link" id="wysiwyg-link"><svg width="70%" height="100%" id="i-link" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" fill="none" stroke="currentcolor" stroke-linecap="round" stroke-linejoin="round" stroke-width="6.25%">   <path d="M18 8 C18 8 24 2 27 5 30 8 29 12 24 16 19 20 16 21 14 17 M14 24 C14 24 8 30 5 27 2 24 3 20 8 16 13 12 16 11 18 15" /></svg>' +
                    '<div class="wysiwyglinkform" tabindex="1" hidden>' +
                        '<div><input id="wysiwygklinkurl" placeholder="LINK ADDRESS"></div>' +
                        '<div><input id="wysiwygklinktext" placeholder="(OPTIONAL) TEXT"></div>' +
                    '</div>' +
                '</button>' +
              '</div> ',
    link: (scope, elem, attrs, ngModel) => {
        let editorelement = elem.children()[0];
        let placeholderelement = elem.children()[1];
        let buttonselement = elem.children()[2];
        let eventListeners = new EventListeners();

        buttonselement.hidden = true;
        let buttons = {};
        for (let i=0; i<buttonselement.children.length; i++) {
            let button = buttonselement.children[i];
            let name = button.id.split('-')[1];
            eventListeners.add(button, "mousedown", function () {scope.vm.blurBlocked = true;});
            if (name !== "color" || name !== "link") {
                eventListeners.add(button, "mouseup", function () {editor.openPopup(); scope.vm.blurBlocked = false;});
            }
            buttons[name] = button;
        }

        placeholderelement.innerHTML = scope.placeholder;

        var options = {
            element: editorelement,
            onPlaceholder: placeholderEvent,
            onKeyDown: function( key, character, shiftKey, altKey, ctrlKey, metaKey ) {
                                if (ctrlKey || metaKey) {
                                    if (character.toLowerCase() === "b") {
                                        console.log("bold hotkey");
                                        editor.bold();
                                        return false;
                                    }
                                    else if (character.toLowerCase() === "i") {
                                        console.log("italic hotkey");
                                        editor.italic();
                                        return false;
                                    }
                                    else if (character.toLowerCase() === "u") {
                                        console.log("underline hotkey");
                                        editor.underline();
                                        return false;
                                    }

                                }
                        },
            onSelection: function( collapsed, rect, nodes, rightclick ) {
                            console.log("Is inside table: "+isInsideTable(nodes));
                            let colors = getCurrentColors(nodes);
                            if (colors.length == 1) {
                                buttons["color"].children[0].style.color = colors[0];
                            } else {
                                buttons["color"].children[0].style.color = 'rgba(0,0,0,0.95)';
                            }
                        },
        };

        var editor = wysiwyg(options);


        // Attach existing $viewValue to editor
        ngModel.$render = () => {
            if (ngModel.$viewValue) {
                editor.setHTML(ngModel.$viewValue);
                placeholderelement.hidden = true;
            }
        };

        function placeholderEvent(visible) {
            if (document.activeElement !== editorelement || !visible) {
                placeholderelement.hidden = !visible;
                editorelement.hidden = visible;
            }
        }

        function getTextFromHTML(html) {
            html = html.replace(/<\/?(br|ul|ol|strong|em|li|h1|h2|h3|h4|p|div)[^>]*>/g, '');
            return html;
        }

        function blur(e) {
            if (!scope.vm.blurBlocked) {
                if (getTextFromHTML(editor.getHTML()) === "") {
                    editor.setHTML("")
                    placeholderEvent(true);
                }
                buttonselement.hidden = true;
                closeLinkForm(true, null);
            }
        }

        function focus() {
            placeholderEvent(false);
            editorelement.focus();
            buttonselement.hidden = false;
        }


        scope.vm.sourcemode = false;
        scope.vm.source = "";
        function toggleSource() {
            var e = editor;

            if (scope.vm.sourcemode) {
                e.setHTML(scope.vm.source)
            } else {
                scope.vm.source = e.getHTML();
                e.setHTML(scope.vm.source.replace(/</g, "&lt;").replace(/>/g, "&gt;"))
            }
            e.readOnly(!scope.vm.sourcemode)
            scope.vm.sourcemode = !scope.vm.sourcemode;
            for (let btn in buttons) {
                if (btn !== "src") {
                    buttons[btn].disabled = e.readOnly();
                }
            }
        }

        eventListeners.add(editorelement, "blur", blur);
        eventListeners.add(editorelement, "focus", focus);
        eventListeners.add(placeholderelement, "click", focus);
        try {
            eventListeners.add(buttons["src"], "click", toggleSource);
        } catch(e) {}
        eventListeners.add(buttons["bold"], "click", editor.bold);
        eventListeners.add(buttons["italic"], "click", editor.italic);
        eventListeners.add(buttons["underline"], "click", editor.underline);
        eventListeners.add(buttons["orderedList"], "click", () => {editor.insertList(true)});
        eventListeners.add(buttons["unorderedList"], "click", () => {editor.insertList(false)});
        eventListeners.add(buttons["heading1"], "click", () => {editor.format("h1")});
        eventListeners.add(buttons["heading2"], "click", () => {editor.format("h2")});
        eventListeners.add(buttons["paragraph"], "click", () => {editor.format("div")});
        eventListeners.add(buttons["removeFormat"], "click", editor.removeFormat);


        let picker = addColorPicker(buttons["color"]);

        picker.on("pickerClosed", () => {editor.closePopup(); scope.vm.blurBlocked=false;});
        picker.on('colorChosen', function(color, targetElem) {editor.closePopup(); editor.forecolor(color); editor.openPopup();});



        // Update state on certain triggering events
        var setState = function() {
            console.log("Setting state")
            scope.$evalAsync(ngModel.$setViewValue(editor.getHTML()))
        };

        // let stateTriggeringEvents = ["keyup", "input", "drop", "cut", "paste", "blur", "focus"];
        let stateTriggeringEvents = ["input"];
        for (let i=0; i<stateTriggeringEvents.length; i++) {
            let ev = stateTriggeringEvents[i];
            eventListeners.add(editorelement, ev, () => {setTimeout(setState(), 0)});
        }

        // DEBUG: Log events
        let logEvents = ["beforeunload", "blur", "click", "cut", "dbclick", "drop", "focus", "hashchange", "input",
                         "input", "keypress", "keyup", "load", "mousedown", "mouseup", "paste", "popstate", "propertychange",
                         "resize", "scroll", "selectionchange", "textinput"]
        function logEvent(e) {
            // console.log(e.type + " triggered")
        }
        for (let i=0; i<logEvents.length; i++) {
            let ev = logEvents[i];
            eventListeners.add(editorelement, ev, logEvent);
        }

        function handleLinkForm(e) {
            console.log("handleLinkForm")
            console.log(e);
            let src = e.srcElement;
            console.log(src.nodeName)
            if (src.id === "wysiwyg-link") {
                let linkform = src.children[0]
                if (linkform.hidden) {
                    console.log(editor.getSelectedHTML())
                    editor.openPopup(); // Save selection, to later add link at right location
                    console.log(editor.getSelectedHTML())
                    linkform.hidden = false;
                    console.log(editor.getSelectedHTML())
                } else {
                    console.log("Forcing close link form")
                    closeLinkForm(true, e)
                }

            } else if (src.nodeName === "INPUT") {
                // editor.openPopup(); // Save selection, to later add link at right location
                console.log(e)
                if (typeof e.type === "click") {
                    src.focus()
                } else if (e.type === "keyup") {
                    if (e.key === "Escape") {
                        closeLinkForm(true, e)
                    } else if (e.key === "Enter") {

                        // Get url
                        let url = buttons["link"].children[0].children[0].children[0].value;
                        console.log(url);
                        if (!url.startsWith("http://")) {
                            url = "http://"+url;
                        }

                        // Get link text
                        let linktext = buttons["link"].children[0].children[1].children[0].value;
                        linktext = linktext !== "" ? linktext: url;
                        console.log(url);

                        editor.insertHTML('<div><a href="'+url+'" target="'+url+'"><span>'+linktext+'</span></a></div>');
                        closeLinkForm(true, e)
                    }
                    console.log(e)
                }
            }
        }

        function closeLinkForm(force, e) {

            console.log("closeLinkForm")
            console.log(force)
            console.log(e)
            console.log(document.activeElement)
            if (!force && buttons["link"].contains(document.activeElement)) {
                // Link form is still active
                return;
            }
            let linkform = buttons["link"].children[0];
            linkform.hidden = true;

            // Clear inputs
            let inputs = linkform.getElementsByTagName("input");
            for (let i=0; i<inputs.length; i++) {
                inputs[i].value = "";
            }

            console.log("Close popup")
            console.log(editor.getSelectedHTML())
            editor.closePopup().collapseSelection()
            scope.vm.blurBlocked = false;
        }

        // eventListeners.add(buttons["link"], "click", handleLinkForm);
        eventListeners.add(buttons["link"], "click", handleLinkForm);
        // eventListeners.add(buttons["link"].children[0], "blur", (e) => setTimeout(closeLinkForm, 1, false, e));
        // eventListeners.add(buttons["link"].children[0], "blur", closeLinkForm);
        let linkinputs = buttons["link"].getElementsByTagName("input");
        for (let i=0; i<linkinputs.length; i++) {
            // eventListeners.add(linkinputs[i], "blur", closeLinkForm);
            eventListeners.add(linkinputs[i], "blur", (e) => {setTimeout(closeLinkForm, 1, false, e)});
            eventListeners.add(linkinputs[i], "keyup", handleLinkForm);
        }
        // eventListeners.add()
        // eventListeners.add(buttons["link"].children[0], "blur", closeLinkForm);
        //  for (let i=0; i<buttons["link"].children.length; i++)
        //     eventListeners.add(buttons["link"].children[i], "blur", closeLinkForm);
        for (let s in editor) {
            console.log(s)
        }



        scope.$on('$destroy', function () {eventListeners.removeAll;});




        //
        // // properties:
        // wysiwygeditor.getElement();
        // wysiwygeditor.getHTML(); -> 'html'
        // wysiwygeditor.setHTML( html );
        // wysiwygeditor.getSelectedHTML(); -> 'html'|false
        // wysiwygeditor.sync();
        // wysiwygeditor.readOnly(); // -> query
        // wysiwygeditor.readOnly( true|false );
        //
        // // selection and popup:
        // wysiwygeditor.collapseSelection();
        // wysiwygeditor.expandSelection( preceding, following );
        // wysiwygeditor.openPopup(); -> popup-handle
        // wysiwygeditor.closePopup();

        // wysiwygeditor.removeFormat();
        // wysiwygeditor.bold();
        // wysiwygeditor.italic();
        // wysiwygeditor.underline();
        // wysiwygeditor.strikethrough();
        // wysiwygeditor.forecolor( color );
        // wysiwygeditor.highlight( color );
        // wysiwygeditor.fontName( fontname );
        // wysiwygeditor.fontSize( fontsize );
        // wysiwygeditor.subscript();
        // wysiwygeditor.superscript();
        // wysiwygeditor.align( 'left'|'center'|'right'|'justify' );
        // wysiwygeditor.format( tagname );
        // wysiwygeditor.indent( outdent );
        // wysiwygeditor.insertLink( url );
        // wysiwygeditor.insertImage( url );
        // wysiwygeditor.insertHTML( html );
        // wysiwygeditor.insertList( ordered );
        //

    }
})

export class WysiwygEditorController {}


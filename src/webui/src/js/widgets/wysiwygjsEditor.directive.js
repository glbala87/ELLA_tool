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



@Directive({
    selector: 'wysiwyg-editor',
    scope: {
        placeholder: '@?',
        ngModel: '=',
        ngDisabled: '=?'
    },
    require: '?ngModel', // get a hold of NgModelController
    template: '<div class="wysywygeditor" ng-disabled="vm.ngDisabled" ng-model="comment.model.comment"></div>' +
              '<div class="wysywygplaceholder"></div> ' +
              '<div class="wysiwygbuttons">' +
                '<button class="wysywgbutton" id="wysywyg-src">&lt;&gt;</button>' +
                '<button class="wysywgbutton" id="wysywyg-bold">B</button>' +
                '<button class="wysywgbutton" id="wysywyg-italic">I</button>' +
                '<button class="wysywgbutton" id="wysywyg-underline">U</button>' +
                '<button class="wysywgbutton" id="wysywyg-heading1">H1</button>' +
                '<button class="wysywgbutton" id="wysywyg-heading2">H2</button>' +
                '<button class="wysywgbutton" id="wysywyg-paragraph">P</button>' +
                '<button class="wysywgbutton" id="wysywyg-orderedList">ol</button>' +
                '<button class="wysywgbutton" id="wysywyg-unorderedList">ul</button>' +
                '<button class="wysywgbutton" id="wysywyg-removeFormat">Tx</button>' +
              '</div> ' +
              '<div class="wysywygdebug"></div> ',
    link: (scope, elem, attrs, ngModel) => {
        let editorelement = elem.children()[0];
        let placeholderelement = elem.children()[1];
        let buttonselement = elem.children()[2];
        let debugelement = elem.children()[3];
        let eventListeners = new EventListeners();


        let buttons = {};
        for (let i=0; i<buttonselement.children.length; i++) {
            let button = buttonselement.children[i];
            eventListeners.add(button, "mousedown", function() {scope.vm.blurBlocked=true;});
            eventListeners.add(button, "mouseup", function() {scope.vm.blurBlocked=false;});
            buttons[button.id.split('-')[1]] = button;
        }

        placeholderelement.innerHTML = scope.placeholder;

        var options = {
            element: editorelement,
            onKeyPress: function( key, character, shiftKey, altKey, ctrlKey, metaKey ) {
                                console.log( character+' key pressed' );
                        },
            onSelection: function( collapsed, rect, nodes, rightclick ) {
                            console.log(editor.getHTML().replace(/</g, "&lt;").replace(/>/g, "&gt;"))
                            debugelement.innerHTML = editor.getHTML().replace(/</g, "&lt;").replace(/>/g, "&gt;");
                            console.log( 'selection rect('+rect.left+','+rect.top+','+rect.width+','+rect.height+'), '+nodes.length+' nodes' );
                        },
            onPlaceholder: placeholderEvent,
        };


        var editor = wysiwyg(options);
        editor.setHTML('<strong>foobar</strong>' );

        function placeholderEvent(visible) {
            if (document.activeElement !== editorelement || !visible) {
                console.log("placeholder event")
                placeholderelement.hidden = !visible;
                editorelement.hidden = visible;
            }
        }


        function blur(e) {
            if (!scope.vm.blurBlocked) {
                // if (e.srcElement === edit)
                console.log(e)
                console.log("blur triggered")
                console.log(editorelement.innerHTML.replace(/\s/g, "").replace(/<\/?br>/g, ""))
                if (editorelement.innerHTML.replace(/\s/g, "").replace(/<\/?br>/g, "") === "") {
                    placeholderEvent(true);
                }
                buttonselement.hidden = true;
            }
        }

        function focus() {
            console.log("focus triggered")
            placeholderEvent(false)
            editorelement.focus()
            buttonselement.hidden = false;
        }

        scope.vm.sourcemode = false;
        scope.vm.source = "";
        function showSource() {
            var e = editor;

            if (scope.vm.sourcemode) {
                console.log(e)
                e.setHTML(scope.vm.source)
                e.readOnly(false);
                scope.vm.sourcemode = false;
            } else {
                console.log(e)
                scope.vm.source = e.getHTML();
                e.setHTML(scope.vm.source.replace(/</g, "&lt;").replace(/>/g, "&gt;"))
                e.readOnly(true)
                scope.vm.sourcemode = true;
            }
        }


        eventListeners.add(editorelement, "blur", blur);
        eventListeners.add(editorelement, "focus", focus);
        eventListeners.add(placeholderelement, "click", focus);

        eventListeners.add(buttons["src"], "click", showSource);
        eventListeners.add(buttons["bold"], "click", editor.bold);
        eventListeners.add(buttons["italic"], "click", editor.italic);
        eventListeners.add(buttons["underline"], "click", editor.underline);
        eventListeners.add(buttons["orderedList"], "click", () => {editor.insertList(true)});
        eventListeners.add(buttons["unorderedList"], "click", () => {editor.insertList(false)});
        eventListeners.add(buttons["heading1"], "click", () => {editor.format("h1")});
        eventListeners.add(buttons["heading2"], "click", () => {editor.format("h2")});
        eventListeners.add(buttons["paragraph"], "click", editor.removeFormat);
        eventListeners.add(buttons["removeFormat"], "click", editor.removeFormat);

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


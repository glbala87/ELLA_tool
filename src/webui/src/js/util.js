/* jshint esnext: true */


// Export angular functions that we use so it's easier to replace later
export let deepEquals = angular.equals;
export let deepCopy = angular.copy;
export let UUID = function generateUUID () { // http://stackoverflow.com/a/8809472
    var d = new Date().getTime();
    if (typeof performance !== 'undefined' && typeof performance.now === 'function'){
        d += performance.now(); //use high-precision timer if available
    }
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
        var r = (d + Math.random() * 16) % 16 | 0;
        d = Math.floor(d / 16);
        return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
    });
}

export let printedFileSize = function(size) {
    var i = Math.floor( Math.log(size) / Math.log(1024) );
    if (i > 2) i = 2;
    return ( size / Math.pow(1024, i) ).toFixed(2) * 1 + ' ' + ['B', 'kB', 'MB'][i];
}

/**
 * example: hasDataAtKey({'person': {'name': 'Dave', 'age': 23}}, 'person', 'age') returns true
 *
 * @param container
 * @param keys one or more strings
 * @returns true if container has a value at the object path given by the keys argument
 */
export function hasDataAtKey(container, ...keys) {
        if (keys.length < 1) {
            return false;
        }

        // recurse into the container using a shrinking list of keys
        let first_key = keys[0]
        if (container[first_key] !== undefined) {
            return (1 === keys.length) ? true : hasDataAtKey(container[first_key], ...keys.slice(1));
        } else {
            return false;
        }
    }


/** Class to contain eventlisteners, so they can be detached using removeAll */
export class EventListeners {
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

/* jshint esnext: true */
import angular from 'angular'
import sanitizeHtml from 'sanitize-html'

// Export angular functions that we use so it's easier to replace later
export let deepEquals = angular.equals
export let deepCopy = angular.copy
export let UUID = function generateUUID() {
    // http://stackoverflow.com/a/8809472
    var d = new Date().getTime()
    if (typeof performance !== 'undefined' && typeof performance.now === 'function') {
        d += performance.now() //use high-precision timer if available
    }
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = (d + Math.random() * 16) % 16 | 0
        d = Math.floor(d / 16)
        return (c === 'x' ? r : (r & 0x3) | 0x8).toString(16)
    })
}

export let printedFileSize = function(size) {
    var i = Math.floor(Math.log(size) / Math.log(1024))
    if (i > 2) i = 2
    return (size / Math.pow(1024, i)).toFixed(2) * 1 + ' ' + ['B', 'kB', 'MB'][i]
}

export function chrToContigRef(chr) {
    const chrContigRef = {
        2: 'NC_000002.11',
        1: 'NC_000001.10',
        3: 'NC_000003.11',
        4: 'NC_000004.11',
        5: 'NC_000005.9',
        6: 'NC_000006.11',
        7: 'NC_000007.13',
        8: 'NC_000008.10',
        9: 'NC_000009.11',
        10: 'NC_000010.10',
        11: 'NC_000011.9',
        12: 'NC_000012.11',
        13: 'NC_000013.10',
        14: 'NC_000014.8',
        15: 'NC_000015.9',
        16: 'NC_000016.9',
        17: 'NC_000017.10',
        18: 'NC_000018.9',
        19: 'NC_000019.9',
        20: 'NC_000020.10',
        21: 'NC_000021.8',
        22: 'NC_000022.10',
        X: 'NC_000023.10',
        Y: 'NC_000024.9',
        //https://www.ncbi.nlm.nih.gov/nuccore/251831106
        MT: 'NC_012920.1'
    }
    return chrContigRef[chr]
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
        return false
    }

    // recurse into the container using a shrinking list of keys
    let first_key = keys[0]
    if (container[first_key] !== undefined) {
        return 1 === keys.length ? true : hasDataAtKey(container[first_key], ...keys.slice(1))
    } else {
        return false
    }
}

/** Class to contain eventlisteners, so they can be detached using removeAll */
export class EventListeners {
    constructor() {
        this.eventListeners = []
    }

    add(el, type, func) {
        el.addEventListener(type, func)
        this.eventListeners.push({ element: el, type: type, function: func })
    }

    remove(el, type, func) {
        el.removeEventListener(type, func)
    }

    removeAll() {
        for (let i = 0; i < this.eventListeners.length; i++) {
            let el = this.eventListeners[i]
            this.remove(el.element, el.type, el.function)
        }
    }
}

export function sanitize(dirtyHTML) {
    return sanitizeHtml(dirtyHTML, {
        allowedTags: [
            'h1',
            'h2',
            'h3',
            'h4',
            'h5',
            'h6',
            'blockquote',
            'p',
            'a',
            'ul',
            'ol',
            'nl',
            'li',
            'b',
            'i',
            'font',
            'strong',
            'em',
            'strike',
            'u',
            'code',
            'hr',
            'br',
            'div',
            'table',
            'thead',
            'caption',
            'tbody',
            'tr',
            'th',
            'td',
            'pre',
            'span'
        ],
        allowedAttributes: {
            '*': ['style'],
            font: ['color'],
            a: ['href', 'name', 'target']
        },
        allowedStyles: {
            // Allow basic style options
            '*': {
                // Match HEX and RGB
                color: [
                    /^[a-z]+$/,
                    /^\#(0x)?[0-9a-f]+$/i,
                    /^rgb\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)$/
                ],
                'background-color': [
                    /^\#(0x)?[0-9a-f]+$/i,
                    /^rgb\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)$/
                ],
                background: [/^\#(0x)?[0-9a-f]+$/i, /^[a-z]+$/i],
                'text-align': [/^left$/, /^right$/, /^center$/]
            }
        }
        // We don't currently allow img itself by default, but this
        // would make sense if we did
        // img: ['src']
    })
}

// Get nested items in object.
// Used like
// let obj = {a: {b: {c: 1}}}
// getNested(obj, "a.b.c") // Returns 1
// getNested(obj, "a") // Returns {b: {c: 1}} (obj.a)
export function getNested(obj, key) {
    if (typeof key === 'string') {
        key = key.split('.')
    }
    let nextKey = key[0]
    let remainingKeys = key.slice(1, key.length)
    if (!(nextKey in obj)) {
        return
    } else if (remainingKeys.length) {
        return getNested(obj[nextKey], remainingKeys)
    } else {
        return obj[nextKey]
    }
}

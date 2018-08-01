/* jshint esnext: true */

import { Directive } from '../../ng-decorators'

/**
 * Display a value from the genepanel. Only the the values that can be overriden in the config part of the genepanel
 * can be displayed in this directive.
 *
 * Usage: <gpv source="..." display="inheritance"></gpv>
 * where source is an expression returning a dict. See webui/src/js/model/analysis.js#getGenepanelValues
 *
 * If display="freq_cutoff" both lo_freq_cutoff and hi_freq_cutoff are displayed when either is overridsen
 * or mode is '!' or '_'
 */

@Directive({
    selector: 'gpv',
    scope: {
        source: '=',
        display: '@',
        prefix: '@', // the character to display in front of the value
        mode: '@' // !=always display value (with override indication),
        // _=always display (without override indication),
        // ?=display only when override (default)
    },
    templateUrl: 'ngtmpl/genepanelvalue.ngtmpl.html'
})
export class GenepanelValueController {
    constructor() {
        this.mode = typeof this.mode == 'undefined' ? '?' : this.mode // make '?' the default
    }

    getValue() {
        if (this.display === 'last_exon') {
            return this.source[this.display] ? 'LEI' : 'LENI'
        } else if (this.display === 'freq_cutoffs_external') {
            return `${this.source['freq_cutoffs'].external.lo_freq_cutoff}/${
                this.source['freq_cutoffs'].external.hi_freq_cutoff
            }`
        } else if (this.display === 'freq_cutoffs_internal') {
            return `${this.source['freq_cutoffs'].internal.lo_freq_cutoff}/${
                this.source['freq_cutoffs'].internal.hi_freq_cutoff
            }`
        }
        return this.source[this.display]
    }

    shouldDisplay() {
        if (this.mode === '_' || this.mode === '!') {
            return true
        } else if (this.mode === '?') {
            return this.isOverridden()
        }
        return true
    }

    isOverridden() {
        if (this.mode === '_') {
            return false
        }
        return this.source['_overridden'].includes(this.display)
    }
}

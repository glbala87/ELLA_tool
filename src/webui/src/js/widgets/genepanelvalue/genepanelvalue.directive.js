/* jshint esnext: true */

import {Directive} from '../../ng-decorators';

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
        source:  '&',
        display: '@',
        prefix:  '@', // the character to display in front of the value
        mode:    '@'  // !=always display value (with override indication),
                      // _=always display (without override indication),
                      // ?=display only when override (default)
    },
    template: `<ng-include src="::vm.getTemplate()"></ng-include>`
})
export class GenepanelValueController {



    constructor() {
        this.freq = null; // used when display=freq_cutoff (a composite of lo and hi values)
        this.singleItem = null; // not composite

        this.mode = (typeof(this.mode) == 'undefined' ? '?' : this.mode); // make '?' the default
        this.v = null; // null values won't be displayed
        this.gp_values = this.source(); // get the values

        // calculate value
        switch (this.display) {
            case 'freq_cutoff':
                const lo = this._calculate(this.gp_values['lo_freq_cutoff'], '!');
                const hi = this._calculate(this.gp_values['hi_freq_cutoff'], '!');
                this.freq = {
                    'lo': lo,
                    'hi': hi,
                    'show': (this.mode == '!' || this.mode == '_') || (lo.override || hi.override)
                };
                break;
            default:
                this.singleItem =  this._calculate (this.gp_values[this.display], this.mode);
                break;
        }

        // convert values
        switch (this.display) {
            case 'last_exon':
                this.singleItem['v'] = (this.singleItem['v'] == null ? null : (this.singleItem['v'] ? 'LEI': 'LENI') );
                break;
        }
    }

    // return a dict with value and boolean indicating override
    _calculate(value, mode) {
        if (typeof(value) == 'object') { // an override value
            return {'override': mode != '_', 'v': value['value']}; // sometimes we don't want icing
        } else {
            return {'override': false, 'v': (mode == '?' ? null : value)};
        }
    }

    getTemplate() {
        switch (this.display) {
            case 'freq_cutoff':
                return 'ngtmpl/genepanelvalue.freq.ngtmpl.html';
                break;
            default:
                return 'ngtmpl/genepanelvalue.ngtmpl.html';
        }
    }

}

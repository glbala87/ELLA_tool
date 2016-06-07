/* jshint esnext: true */

import {Directive} from '../../ng-decorators';

/**
 * Display a value from the genepanel. Only the the values that can be overriden in the config part of the genepanel
 * can be displayed in this directive.
 *
 * Usage: <gpv source="..." fields="inheritance"></gpv>
 * where source is an expression returning a dict. See webui/src/js/model/analysis.js#getGenepanelValues
 *
 * TODO: for frequency cutoff, do we need to show both lo and hi if any of them are overriden?
 */

@Directive({
    selector: 'gpv',
    scope: {
        source:  '&',
        display: '@',
        prefix:  '@', // the character to display in front of the value
        mode:    '@'  // !=always display value, _=always display (without override indication),
                      // ?=display only when override (default)
    },
    templateUrl: 'ngtmpl/genepanelvalue.ngtmpl.html'

})
export class GenepanelValueController {

    constructor() {
        this.mode = (typeof(this.mode) == 'undefined' ? '?' : this.mode); // make '?' the default
        this.v = null; // null values won't be displayed
        this.gp_values = this.source(); // get the values
        this.wrapper = this.gp_values[this.display];
        if (typeof(this.wrapper) == 'object') { // an override value
            this.override = this.mode != '_'; // sometimes we don't want icing
            this.v = this.wrapper['value'];
        } else {
            this.override = false;
            this.v = (this.mode == '?' ? null : this.wrapper);
        }

        // convert values
        switch (this.display) {
            case 'last_exon':
                this.v = (this.v == null ? null : (this.v ? 'LEI': 'LENI') );
                break;
        }
    }

}

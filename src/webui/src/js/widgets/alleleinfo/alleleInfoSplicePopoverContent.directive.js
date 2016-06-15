/* jshint esnext: true */

import {Directive, Inject} from '../../ng-decorators';

@Directive({
    selector: 'allele-info-splice-popover',
    scope: {
        allele: '=',
        t: '='
    },
    templateUrl: 'ngtmpl/alleleInfoSplicePopoverContent.ngtmpl.html'
})
@Inject()
export class alleleInfoSplicePopover {

    constructor() {}

    hasContent() {
        return this.allele.annotation.filtered.some(t => 'Splice' in t);
    }

    getText(effect) {
        var msg;
        switch (effect.splice_Effect)
        {
            case "not_transcribed":
                msg = "The variant occurs outside the transcript.";
                break;
            case "consensus_not_affected":
                msg = `The closest splice site nucleotide sequence in this transcript is not affected by the variant.
                       The strength of the site is unaffected (MaxEntScan: ${effect['splice_MaxEntScan_wild']}).`;
                break;
            case "predicted_lost":
                msg = `Closest splice site in transcript is predicted to be lost (MaxEntScan decreases from 
                       ${effect['splice_MaxEntScan_wild']} to ${effect['splice_MaxEntScan_mut']})`;
                break;
            case "predicted_conserved":
                msg = `Closest splice site in transcript is predicted to be conserved (MaxEntScan decreases from 
                       ${effect['splice_MaxEntScan_wild']} to ${effect['splice_MaxEntScan_mut']})`;
                break;
            case "de_novo":
                msg = `Putative de novo splice site at this position (MaxEntScan: from 
                       ${effect['splice_MaxEntScan_wild']} to ${effect['splice_MaxEntScan_mut']}).
                       Closest authentic splice site in transcript is ${effect['splice_dist']}
                       bp away (MaxEntScan: ${effect['splice_MaxEntScan_closest']})`;
                break;
            case "splice_donor_variant":
                msg = "The mutation occurs with +1/2 bp of donor site.";
                break;
            case "splice_acceptor_variant":
                msg = "The mutation occurs with +1/2 bp of acceptor site.";
                break;
            case "NA":
                msg = "The effect could not be computed by the predictor.";
                break;
            default:
                msg = "Unknown annotation.";
                break;
        }
        return msg;
    }
}

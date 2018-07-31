/* jshint esnext: true */

import { Directive, Inject } from '../../ng-decorators'
import template from './alleleInfoSplicePopoverContent.ngtmpl.html'

@Directive({
    selector: 'allele-info-splice-popover',
    scope: {
        allele: '=',
        t: '='
    },
    template
})
@Inject()
export class alleleInfoSplicePopover {
    constructor() {}

    hasContent() {
        return this.allele.annotation.filtered.some((t) => 'splice' in t)
    }

    getText(effect) {
        var msg
        switch (effect.effect) {
            case 'not_transcribed':
                msg = 'The variant occurs outside the transcript.'
                break
            case 'consensus_not_affected':
                msg = `The closest splice site nucleotide sequence in this transcript is not affected by the variant.
                       The strength of the site is unaffected (MaxEntScan: ${
                           effect['maxentscan_wild']
                       }).`
                break
            case 'predicted_lost':
                msg = `Closest splice site in transcript is predicted to be lost (MaxEntScan decreases from
                       ${effect['maxentscan_wild']} to ${effect['maxentscan_mut']})`
                break
            case 'predicted_conserved':
                msg = `Closest splice site in transcript is predicted to be conserved (MaxEntScan decreases from
                       ${effect['maxentscan_wild']} to ${effect['maxentscan_mut']})`
                break
            case 'de_novo':
                msg = `Putative de novo splice site at this position (MaxEntScan: from
                       ${effect['maxentscan_wild']} to ${effect['maxentscan_mut']}).
                       Closest authentic splice site in transcript is ${effect['dist']}
                       bp away (MaxEntScan: ${effect['maxentscan_closest']})`
                break
            case 'splice_donor_variant':
                msg = 'The mutation occurs with +1/2 bp of donor site.'
                break
            case 'splice_acceptor_variant':
                msg = 'The mutation occurs with +1/2 bp of acceptor site.'
                break
            case 'NA':
                msg = 'The effect could not be computed by the predictor.'
                break
            default:
                msg = 'Unknown annotation.'
                break
        }
        return msg
    }
}

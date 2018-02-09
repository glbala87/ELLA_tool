/* jshint esnext: true */

import {Directive, Inject} from '../ng-decorators';
import {AlleleStateHelper} from '../model/allelestatehelper';
import {deepCopy} from '../util'

@Directive({
    selector: 'allele-sidebar',
    templateUrl: 'ngtmpl/alleleSidebar.ngtmpl.html',
    scope: {
        genepanel: '=',
        alleles: '=',  // Allele options: { unclassified: [ {allele: Allele, alleleState: {...}, checkable: true, checked: true ] }, classified: [ ... ] }
        selected: '=', // Selected Allele
        readOnly: '=?' // if readOnly the allele can't be added to report
    },
})
@Inject('$scope', 'orderByFilter', 'Config')
export class AlleleSidebarController {

    constructor($scope, orderByFilter, Config) {
        this.config = Config.getConfig();

        this.orderBy = {
            'classified': [undefined, false],
            'unclassified': [undefined, false]
        }

        this.orderByFilter = orderByFilter;

        $scope.$watch(
            () => this.alleles,
            () => {
                this.classified_alleles = this.orderByFilter(this.alleles.classified, (allele) => {return this.sort(allele, this.orderBy.classified[0])}, this.orderBy.classified[1]);
                this.unclassified_alleles = this.orderByFilter(this.alleles.unclassified, (allele) => {return this.sort(allele, this.orderBy.unclassified[0])}, this.orderBy.unclassified[1]);
            }
        )
    }


    sort(allele_obj, orderBy) {
        let allele = allele_obj.allele;
        switch (orderBy) {
            case "inheritance":
                return this.getInheritance(allele);
            case "gene":
                return allele.annotation.filtered[0].symbol;
            case "hgvsc":
                let s = allele.annotation.filtered[0].HGVSc_short || allele.getHGVSgShort();
                let d = parseInt(s.match(/[cg]\.(\d+)/)[1]);
                return d
            case "consequence":
                let consequence_priority = this.config.transcripts.consequences;
                let consequences = allele.annotation.filtered.map(t => t.consequences);
                consequences = [].concat.apply([], consequences);
                let consequence_indices = consequences.map(c => consequence_priority.indexOf(c));
                return Math.min( ...consequence_indices );
            case "homozygous":
                return !this.isHomozygous(allele);
            case "quality":
                return !this.isLowQual(allele);
            case "references":
                return !this.isImportantSource(allele);
            case "3hetAR":
                return !this.is3hetAR(allele);
            default:
                return 0
        }
    }

    sortBy(alleles_selection, sortBy) {
        // Sort alleles_selection (classified/unclassified) by sortBy
        if (this.orderBy[alleles_selection][0] === sortBy) {
            if (!this.orderBy[alleles_selection][1]) {
                this.orderBy[alleles_selection][1] = true;
            } else {
                this.orderBy[alleles_selection] = [undefined, false];
            }
        } else {
            this.orderBy[alleles_selection][0] = sortBy;
        }

        // Update filter on classified and unclassified alleles
        this.classified_alleles = this.orderByFilter(this.alleles.classified, (allele) => {return this.sort(allele, this.orderBy.classified[0])}, this.orderBy.classified[1]);
        this.unclassified_alleles = this.orderByFilter(this.alleles.unclassified, (allele) => {return this.sort(allele, this.orderBy.unclassified[0])}, this.orderBy.unclassified[1]);
    }

    select(allele_option) {
        // We have two modes, multiple checkable or normal radio selectiion (of single allele)

        // Multiple (if 'checkable' === true)
        if (this.isTogglable(allele_option)) {
            allele_option.toggle();
        }
        // Single selection
        else {
            this.selected = allele_option.allele;
        }
    }

    isSelected(allele_option) {
        if (!this.selected) {
            return false;
        }

        let matching = this.selected.id === allele_option.allele.id;

        // If checkable is true, we don't support select mode. Set to null
        if (matching && allele_option.checkable) {
            this.selected = null;
            return false;
        }
        return matching;
    }

    isToggled(allele_option) {
        if (this.isTogglable(allele_option)) {
            return allele_option.isToggled();
        }
        return false;
    }

    isTogglable(allele_option) {
        return allele_option.togglable;
    }

    getSampleType(allele) {
        return allele.samples.map(s => s.sample_type.substring(0, 1)).join('').toUpperCase();
    }

    getSampleTypesFull(allele) {
        return allele.samples.map(s => s.sample_type).join(', ').toUpperCase();
    }

    getConsequence(allele) {
        let consequence_priority = this.config.transcripts.consequences;
        let sort_func = (a, b) => {
            return consequence_priority.indexOf(a) - consequence_priority.indexOf(b);
        }
        return allele.annotation.filtered.map(
            t => t.consequences.sort(sort_func)[0].replace('_variant', '')
        ).join(' | ');
    }

    getInheritance(allele) {
        if (this.genepanel) {
            return this.genepanel.getDisplayInheritance(allele.annotation.filtered[0].symbol);
        }
    }

    getClassification(allele, allele_state) {
        let classification = AlleleStateHelper.getClassification(allele, allele_state);
        if (AlleleStateHelper.isAlleleAssessmentOutdated(allele, this.config)) {
            return `${classification}*`;
        }
        return classification;
    }

    isHomozygous(allele) {
        return allele.samples[0].genotype.homozygous;
    }

    isLowQual(allele) {
        return allele.samples.some(s => s.genotype.needs_verification);
    }

    isNonsense(allele) {
        let nonsense_consequences = [
            "start_lost",
            "initiator_codon_variant",
            "transcript_ablation",
            "splice_donor_variant",
            "splice_acceptor_variant",
            "stop_gained",
            "frameshift_variant"
        ];
        return allele.annotation.filtered.some(t => {
            return nonsense_consequences.some(c => {
                return t.consequences.includes(c);
            });
        });
    }

    isImportantSource(allele) {
        return 'HGMD' in allele.annotation.external &&
               allele.annotation.external.HGMD.tag;
    }

    isMultipleInAlleleGenes(allele) {
        let other_alleles = this.alleles.classified.concat(
            this.alleles.unclassified
        ).map(
            a => a.allele
        ).filter( // Exclude "ourself"
            a => a !== allele
        );
        let other_alleles_genes = [];
        for (let other_allele of other_alleles) {
            other_alleles_genes.push(...other_allele.annotation.filtered.map(f => f.symbol))
        }
        let our_genes = allele.annotation.filtered.map(f => f.symbol);
        return our_genes.some(s => other_alleles_genes.includes(s));
    }

    is3hetAR(allele) {
        if (this.isHomozygous(allele)) return false;
        if (this.isMultipleInAlleleGenes(allele)) return false;
        if (this.isImportantSource(allele)) return false;
        if (this.getInheritance(allele) !== "AR") return false;
        if (this.isNonsense(allele)) return false;
        return true;
    }
}

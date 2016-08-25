/* jshint esnext: true */

import {Directive, Inject} from '../ng-decorators';
import {AlleleStateHelper} from '../model/allelestatehelper';

@Directive({
    selector: 'allele-sidebar',
    templateUrl: 'ngtmpl/alleleSidebar.ngtmpl.html',
    scope: {
        alleles: '=',  // Allele options: { unclassified: [ {allele: Allele, alleleState: {...}, inactive: true, checkable: true, checked: true ] }, classified: [ ... ] }
        selected: '=', // Selected Allele
    },
    link: (scope, element) => {
      let scrollFunction = function() {
        let offset = parseInt(window.pageYOffset);
        if (40 <= offset) {
          element.addClass("higher");
        } else {
          element.removeClass("higher");
        }
      };
      angular.element(window).on("scroll", scrollFunction);
      scope.$on('$destroy', function() {
        angular.element(window).off('scroll', scrollFunction);
      });
    }
})
@Inject()
export class AlleleSidebarController {

    constructor() {
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
        let selected = this.selected === allele_option.allele;
        // If checkable is true, we don't support select mode. Set to null
        if (selected && allele_option.checkable) {
            this.selected = null;
            return false;
        }
        return selected;
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

    getClassification(allele, allele_state) {
        return AlleleStateHelper.getClassification(allele, allele_state);
    }
}

/* jshint esnext: true */

import {Directive, Inject} from '../ng-decorators';

@Directive({
    selector: 'allele-list',
    scope: {
        alleleItems: '=', // [{genepanel: {}, allele: Allele}, ...]
        onSelect: '&?' // Selection callback. Used to clear search
    },
    templateUrl: 'ngtmpl/alleleList.ngtmpl.html',
})
@Inject('$scope',
        'Sidebar',
        'User',
        'Analysis',
        'InterpretationResource',
        'InterpretationOverrideModal',
        'toastr')
class AlleleListWidget {

    constructor($scope,
                Sidebar,
                User,
                InterpretationResource,
                InterpretationOverrideModal,
                toastr) {
        this.location = location;
        this.user = User;
        this.interpretationResource = InterpretationResource;
        this.interpretationOverrideModal = InterpretationOverrideModal;
        this.toastr = toastr;

        $scope.$watchCollection(
            () => this.alleleItems,
            () => this.sortItems()
        );
        this.sorted_items = [];
    }


    sortItems() {
        if (!this.alleleItems) { return; }
        this.sorted_items = this.alleleItems.slice(0);
        this.sorted_items.sort(
            firstBy(a => a.allele.annotation.filtered[0].SYMBOL)
            .thenBy(a => {
                if (a.allele.annotation.filtered[0].STRAND > 0) {
                    return a.allele.start_position;
                }
                return -a.allele.start_position;
            })
        );
    }

    abbreviateUser(user) {
      if(Object.keys(user).length != 0) {
        return `${user.first_name.substring(0,1)}. ${user.last_name}`;
      } else {
        return "";
      }
    }

    getReviewComment(item) {
        return item.interpretations[item.interpretations.length-1].review_comment;
    }

    getItemUrl(item) {
        let allele = item.allele;
        return `/variants/${allele.genome_reference}/${allele.chromosome}-${allele.start_position}-${allele.open_end_position}-${allele.change_from}-${allele.change_to}?gp_name=${item.genepanel.name}&gp_version=${item.genepanel.version}`;
    }
}

export default AlleleListWidget;

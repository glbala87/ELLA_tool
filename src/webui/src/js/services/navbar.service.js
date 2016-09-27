/* jshint esnext: true */

import {Service, Inject} from '../ng-decorators';

@Service({
    serviceName: 'Navbar'
})
@Inject()
export class NavbarService {

    /**
     * Service for managing navbar items
     */
    constructor() {
        // item:
        // {
        //  'title': 'Analysis list',
        //  'url': .. (optional)
        // }
        this.items = [];
        this.allele = null;
    }

    clearAllele() {
      this.allele = null;
    }

    setAnalysis(analysis) {
        this.analysis = analysis;
    }

    getAnalysis() {
        return this.analysis;
    }

    clearAnalysis() {
        this.analysis = null;
    }

    setAllele(allele) {
        this.allele = allele;
    }

    getAllele() {
      return this.allele;
    }

    clearItems() {
        this.clearAllele();
        this.clearAnalysis();
        this.items = [];
    }

    replaceItems(items) {
        this.items = items;
    }

    getItems() {
        return this.items;
    }

}

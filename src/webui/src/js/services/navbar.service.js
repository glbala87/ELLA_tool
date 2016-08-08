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
        this.allele = {};
    }

    setAllele(allele) {
      this.allele = allele;
    }

    getAllele() {
      return this.allele;
    }

    clearItems() {
        this.items = [];
    }

    replaceItems(items) {
        this.items = items;
    }

    getItems() {
        return this.items;
    }

}

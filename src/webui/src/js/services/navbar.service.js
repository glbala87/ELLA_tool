/* jshint esnext: true */

import { Service, Inject } from '../ng-decorators'

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
        this.items = []
        this.allele = null
    }

    clearAllele() {
        this.allele = null
    }

    setAllele(allele, genepanel = null) {
        this.allele = allele
        this.genepanel = genepanel
    }

    getAllele() {
        return this.allele
    }

    getGenepanel() {
        return this.genepanel
    }

    clearItems() {
        this.clearAllele()
        this.items = []
    }

    replaceItems(items) {
        this.items = items
    }

    getItems() {
        return this.items
    }
}

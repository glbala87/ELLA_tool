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
        //  'header': 'Go to' (optional),
        //  'title': 'Analysis list',
        //  'url': .. (optional)
        // }
        this.items = [];
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

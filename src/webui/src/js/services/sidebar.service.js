/* jshint esnext: true */

import {Service, Inject} from '../ng-decorators';

@Service({
    serviceName: 'Sidebar'
})
@Inject()
export class SidebarService {

    /**
     * Service for managing the items, title and back options in the sidebar
     */
    constructor() {
        this.title = '';
        this.header = false;
        this.back = {
            title: '',
            url: null
        };
        this.items = [];
    }

    activate(item) {
        for (let i of this.items) {
            i.active = false;
        }
        item.active = true;
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

    setTitle(title, show_header) {
        this.title = title;
        this.header = show_header;
    }

    getTitle() {
        return this.title;
    }

    getHeader() {
        return this.header;
    }

    setBackLink(title, url) {
        this.back.title = title;
        this.back.url = url;
    }

    getBackLink() {
        return this.back;
    }


}

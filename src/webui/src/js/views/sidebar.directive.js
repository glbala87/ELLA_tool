/* jshint esnext: true */

import {Directive, Inject} from '../ng-decorators';

@Directive({
    selector: 'sidebar',
    templateUrl: 'ngtmpl/sidebar.ngtmpl.html'
})
@Inject('Sidebar', 'User')
export class SidebarController {

    constructor(Sidebar, User) {
        this.sidebar = Sidebar;
        this.user = {};
        User.getCurrentUser().then(user => {
            this.user = user;
        });
    }

    activate(item) {
        this.sidebar.activate(item);
    }

    getItems() {
        return this.sidebar.getItems();
    }

    getTitle() {
        return this.sidebar.getTitle();
    }

    showHeader() {
        return this.sidebar.getHeader();
    }

    getBackLink() {
        return this.sidebar.getBackLink();
    }
}

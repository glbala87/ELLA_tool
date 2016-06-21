/* jshint esnext: true */

import {Directive, Inject} from '../ng-decorators';

@Directive({
    selector: 'navbar',
    templateUrl: 'ngtmpl/navbar.ngtmpl.html'
})
@Inject('Navbar', 'User', '$location')
export class NavbarController {

    constructor(Navbar, User, $location) {
        this.navbarService = Navbar;
        this.user = {};
        User.getCurrentUser().then(user => {
            this.user = user;
        });
        this.location = $location;
    }

    getItems() {
        return this.navbarService.getItems();
    }

    isLastItem(item) {
        let idx = this.navbarService.getItems().indexOf(item);
        return  idx === this.navbarService.getItems().length - 1;
    }

    goToItem(item) {
        if (item.url) {
            this.location.path(item.url);
        }
    }

    goToLogin() {
        this.location.path('/login');
    }
}

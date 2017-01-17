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

    abbreviateUser() {
      if(Object.keys(this.user).length != 0) {
        return `${this.user.first_name.substring(0,1)}. ${this.user.last_name}`;
      } else {
        return "";
      }
    }

    hasAllele() {
      return Boolean(this.navbarService.getAllele());
    }

    getAllele() {
      return this.navbarService.getAllele();
    }

    getGenepanel() {
      return this.navbarService.getGenepanel();
    }

    getItems() {
      return this.navbarService.getItems();
    }

    isLastItem(item) {
        let idx = this.navbarService.getItems().indexOf(item);
        return  idx === this.navbarService.getItems().length - 1;
    }

    hasUrl(item) {
      if (item.url) { return true; } else { return false; }
    }

    goToItem(item) {
        if (item.url) {
            this.location.path(item.url);
        }
    }

    isLogin() {
      return this.location.path() == '/login';
    }

    goToLogin() {
        this.location.path('/login');
    }


}

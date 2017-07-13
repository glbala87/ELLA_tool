/* jshint esnext: true */

import {Directive, Inject} from '../ng-decorators';

@Directive({
    selector: 'navbar',
    templateUrl: 'ngtmpl/navbar.ngtmpl.html'
})
@Inject('Navbar', 'User', 'Config', '$location')
export class NavbarController {

    constructor(Navbar, User, Config, $location) {
        this.navbarService = Navbar;
        this.user = User;
        this.config = Config.getConfig();
        this.location = $location;

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

    isLogin() {
      return this.location.path() == '/login';
    }

}

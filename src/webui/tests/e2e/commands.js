function waitForAngular() {
    browser.timeoutsAsyncScript(2000).executeAsync(function(done) {
        if(angular && angular.getTestability) {
            angular.getTestability(document.body).whenStable(done);
        }
        else {
            done();
        }
    });
}

module.exports = function addCommands() {

    browser.addCommand('resetDb', () => {
        let wait_seconds = 15;
        console.log(`Resetting database (waiting ${wait_seconds}s)...`);
        browser.url('/reset?testset=e2e');
        browser.pause(wait_seconds * 1000);
        console.log("Database reset done!");
    });

    browser.addCommand('getClass', (selector) => browser.getAttribute(selector, 'class').split(' '));

    browser.addCommand('waitForAngular', waitForAngular);

}
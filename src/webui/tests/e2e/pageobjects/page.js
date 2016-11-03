class Page {

    open(path) {
        browser.url("http://" + browser.options.baseUrl+ '/' + path);
    }
}

module.exports = Page;
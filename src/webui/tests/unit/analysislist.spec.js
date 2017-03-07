import Analysis from "../../src/js/model/analysis.js"

    describe("list of analyses", function () {

    var scope;
    var elm;

    beforeEach(function() {
        angular.mock.module('workbench');
        angular.mock.module('templates'); // created by karma's ngHtml2JsPreprocessor
    });

    beforeEach(function() {
        angular.mock.module(function ($provide) {
            function myProvider() {
                this.$get = function () {
                    return {
                        getConfig: function() { return 'xxx'},
                        analysis: {priority: {display: []}}
                    };
                }
            }
            $provide.provider('Config', myProvider);

    })
    });

    beforeEach(inject(function ($compile, $rootScope) {
        elm = angular.element("<analysis-list analyses='vm.pending_analyses'></analysis-list>");
        let parent = $rootScope;
        parent.vm = {
            pending_analyses: [
                {
                    'name': 'sample 1',
                    'deposit_date': '2016-08-10',
                    'interpretations': [{'review_comment': 'review for sample 1'}]
                },
                {
                     'name': 'sample 2',
                    'deposit_date': '2016-08-09',
                    'interpretations': [{'review_comment': 'review for sample 2'}]
                }
            ],

        };
        $compile(elm)(parent);
        parent.$digest();
        scope = elm.isolateScope();
    }));

    it("list is expanded", function () {
        expect(elm.find('a')).toBeDefined();
        expect(elm.find('a').length).toBeGreaterThan(1);
    });

;

});

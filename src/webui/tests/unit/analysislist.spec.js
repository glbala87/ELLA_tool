    describe("list of analyses", function () {

    var scope;
    var elm;

    beforeEach(function() {
        angular.mock.module('workbench');
        angular.mock.module('templates'); // created by karma's ngHtml2JsPreprocessor
    });

    beforeEach(inject(function ($compile, $rootScope) {
        elm = angular.element("<analysis-list analyses='vm.pending_analyses'></analysis-list>");
        scope = $rootScope.$new();
        scope.vm = {
            //pending_analyses: [
            //    {'name': 'one', getInterpretationState: function() {return undefined;}},
            //    {'name': 'two', getInterpretationState: function() {return undefined;}}
            //] // two items ng-repeat in the template
            pending_analyses: [undefined] // a single item to kick off ng-repeat in the template
        };

        $compile(elm)(scope);
        scope.$digest();
    }));

    it("list is expanded", function () {
      expect(elm.find('div')).toBeDefined();
      expect(elm.find('div').length).toBeGreaterThan(1);
    });

});

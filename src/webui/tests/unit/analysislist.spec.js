import Analysis from "../../src/js/model/analysis.js"

    describe("list of analyses", function () {

    var scope;
    var elm;

    beforeEach(function() {
        angular.mock.module('workbench');
        angular.mock.module('templates'); // created by karma's ngHtml2JsPreprocessor
    });

    beforeEach(inject(function ($compile, $rootScope) {
        elm = angular.element("<analysis-list analyses='vm.pending_analyses'></analysis-list>");
        let parent = $rootScope;
        parent.vm = { // a single item to kick off ng-repeat in the template
            pending_analyses: [{'deposit_date': '2016-08-10'}, {'deposit_date': '2016-08-09'}]
        };
        $compile(elm)(parent);
        parent.$digest();
        scope = elm.isolateScope();
    }));

    it("list is expanded", function () {
        expect(elm.find('contentbox')).toBeDefined();
        expect(elm.find('contentbox').length).toBeGreaterThan(1);
    });

    describe("when user clicks an analysis", function () {

        it("it returns undefined if already analysed by this user", function () {
            // Setup mocks
            scope.vm.user = {
                getCurrentUserId: () => 1
            };
            let analysis = {
                interpretations: [
                    {
                        user: {
                            id: 1
                        },
                        status: 'Done'
                    },
                    {
                        user: {
                            id: 2
                        },
                        status: 'Done'
                    }
                ]
            };
            expect(scope.vm.clickAnalysis(analysis)).toEqual(undefined);

        });

        it("it opens override modal if analysis is in use by another user", function () {
            // Setup mocks
            scope.vm.user = {
                getCurrentUserId: () => 1
            };
            let analysis = new Analysis({
                interpretations: [
                    {
                        user: {
                            id: 3
                        },
                        status: 'Done'
                    },
                    {
                        user: {
                            id: 2
                        },
                        status: 'In progress'
                    }
                ]
            });

            scope.vm.interpretationOverrideModal = {
                show: () => {
                    return {
                        then: (func) => func("RESULT")
                    }
                }
            };

            spyOn(scope.vm, "overrideAnalysis");
            scope.vm.clickAnalysis(analysis);
            expect(scope.vm.overrideAnalysis).toHaveBeenCalled();


        });

        it("it opens analysis if not Done and not previously analysed by user", function () {

            scope.vm.user = {
                getCurrentUserId: () => 1
            }
            let analysis = new Analysis({
                interpretations: [
                    {
                        status: 'Pending'
                    }
                ]
            });

            spyOn(scope.vm, "openAnalysis");
            scope.vm.clickAnalysis(analysis);
            expect(scope.vm.openAnalysis).toHaveBeenCalled();

        });
    });

});

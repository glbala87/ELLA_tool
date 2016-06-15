
describe("filter", function () {

    var $filter;

    describe("isEmpty", function () {
        var f;

        beforeEach(function () {
            angular.mock.module('workbench');
            inject(
                function (_$filter_) {
                    f = _$filter_("isEmpty");
                });
        });

        xit("throws an error when handed a string", function () {
            expect(f('')).toThrow();
        });

        it("gives true for {}", function () {
            expect(f({})).toBe(true);
        });

        it("gives false for object with keys", function () {
            expect(f({akey: 42})).toBe(false);
        });
    });

    describe("split", function () {
        var f;

        beforeEach(function () {
            angular.mock.module('workbench');
            inject(
                function (_$filter_) {
                    f = _$filter_("split");
                });
        });

        it("gets the first piece", function () {
            expect(f('ab:c', ':', 0)).toBe('ab');
        });

        it("gets the last piece", function () {
            expect(f('ab:c', ':', 1)).toBe('c');
        });

        it("gets undefined when seperator is missing from string", function () {
            expect(f('abc', ':', 1)).toBe(undefined);
        });

        it("gets undefined when seperator is not given", function () {
            expect(f('abc', undefined, 1)).toBe(undefined);
        });
    });

    describe("HGVSc_short", function () {
        var f;

        beforeEach(function () {
            angular.mock.module('workbench');
            inject(
                function (_$filter_) {
                    f = _$filter_('HGVSc_short');
                });
        });

        it("shortens by getting the last part", function() {
            expect(f('abc:def')).toEqual('def');
        });

        it("returns undefined when separator is missing", function() {
            expect(f('abc')).toEqual(undefined);
        });

    });

    describe("HGVSp_short", function () {
        var f;

        beforeEach(function () {
            angular.mock.module('workbench');
            inject(
                function (_$filter_) {
                    f = _$filter_('HGVSp_short');
                });
        });

        it("shortens by getting the last part", function() {
            expect(f('abc:def')).toEqual('def');
        });

        it("returns undefined when seperator is missing", function() {
            expect(f('abc')).toEqual(undefined);
        });

    });


});


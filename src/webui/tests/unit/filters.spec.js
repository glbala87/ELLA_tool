
describe("filter", function () {

    var $filter;

    // '_'  never any decoration
    // '?' show only when overridden in genepanel config
    describe("gp_values", function () {
        var f;

        beforeEach(function () {
            angular.mock.module('workbench');
            inject(
                function (_$filter_) {
                    f = _$filter_("gp_values");
                });
        });

        it("shows default values without decoration", function () {
            expect(f({'inheritance': 'AD', 'hi_freq_cutoff': 0.1, 'lo_freq_cutoff': 0.005},
            ['freq_cutoff','inheritance'])).toBe('0.1/0.005|AD');
        });

        it("shows overridden values with decoration", function () {
            expect(f({'inheritance': {'_type': 'genepanel_value','value': 'AD'}, 'hi_freq_cutoff': 0.1, 'lo_freq_cutoff': 0.005},
            ['freq_cutoff','inheritance'])).toBe('0.1/0.005|*AD*');
        });

        xit("shows value depending on mode", function () {
            expect(f({'inheritance': {'_type': 'genepanel_value','value': 'AD'}, 'hi_freq_cutoff': 0.1, 'lo_freq_cutoff': 0.005},
                ['freq_cutoff!','inheritance:_'])).toBe('AD');
        })

    });

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


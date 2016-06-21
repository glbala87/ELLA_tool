
import AlleleFilter from "../../src/js/services/alleleFilter.service.js"

describe("AlleleFilter service", function () {


    /**
     * return an object having a getConfig function. The function returns an object with frequency cutoffs
     * See config.py
     */
    function makeConfig(freq, signed_cutoffs) {
        var mockConfig = function() {};
        mockConfig.getConfig = function() {
            return {frequencies: {criterias: freq},
                    variant_criteria: {
                        intronic_region: signed_cutoffs
            }};
        };
        return mockConfig;

    }

    it("can be constructed", function () {
        expect(new AlleleFilter(makeConfig({"someKey": 12}))).toBeDefined();
    });

    it("empty list returns empty list ", function () {
        let service = new AlleleFilter(makeConfig({"someKey": 11}));
        let res = service.filterClass1([]);
        expect(res).toEqual([]);
    });


    it("filters on frequency", function () {
        let cutoff = 4;
        let service = new AlleleFilter(makeConfig({a: {suba: cutoff}}));
        let someAlleles = [
            {id: 1, annotation:  {frequencies: {a: {suba: cutoff-1}}}},
            {id: 2, annotation:  {frequencies: {a: {suba: cutoff}}}},
            {id: 3, annotation:  {frequencies: {a: {suba: cutoff+1}}}}
        ];

        expect(service.filterClass1([someAlleles[2]])).toEqual([]);
        expect(service.filterClass1([someAlleles[1], someAlleles[2]]).length).toEqual(1);
        expect(service.filterClass1([someAlleles[1], someAlleles[2]])[0]).toEqual(jasmine.objectContaining({id: 2}));
        expect(service.filterClass1(someAlleles).length).toEqual(2);

    });

    it("intron filter  returns empty for empty", function () {
        let service = new AlleleFilter(makeConfig());
        expect(service.filterIntronicAlleles([])).toEqual([]);


    });

    it("alleles with unknown HGVSc format are kept", function () {
        let service = new AlleleFilter(makeConfig(null, {'-': 210, '+': 60}));
        let someAlleles = [
            {id: 1, annotation: {filtered: [{HGVSc: "some-unknown-format"}, {HGVSc: "NM_007294.3:c.4535-213G>T"}]}},
            {id: 2, annotation: {filtered: [{HGVSc: "NM_007294.3:c.4535-213G>T"}, {HGVSc: "NM_007294.3:c.4535-215G>T"}]}}
        ];

        let res = service.filterIntronicAlleles(someAlleles);
        expect(res.length).toEqual(1);
        expect(res[0]).toEqual(jasmine.objectContaining({id: 1}));

    });

    it("filters on position", function () {
        let service = new AlleleFilter(makeConfig(null, {'-': 210, '+': 60}));
        let someAlleles = [
            {id: 1, help: "both are above threshold", annotation: {filtered: [{HGVSc: "NM_007294.3:c.4535-211G>T"}, {HGVSc: "NM_007294.3:c.4535-213G>T"}]}},
            {id: 2, annotation: {filtered: [{HGVSc: "NM_007294.3:c.4535-200G>T"}, {HGVSc: "NM_007294.3:c.4535-213G>T"}]}},
            {id: 3, help: "both are above threshold", annotation: {filtered: [{HGVSc: "NM_007294.3:c.4535-214G>T"}, {HGVSc: "NM_007294.3:c.4535-215G>T"}]}}
        ];

        let res = service.filterIntronicAlleles(someAlleles);
        expect(res.length).toEqual(1);
        expect(res[0]).toEqual(jasmine.objectContaining({id: 2}));

    });

    it("no filtering when intron config is missing sign", function () {
        let service = new AlleleFilter(makeConfig(null, {'+': 60}));
        let someAlleles = [
            {id: 1, annotation: {filtered: [{HGVSc: "NM_007294.3:c.4535-211G>T"}, {HGVSc: "NM_007294.3:c.4535-213G>T"}]}},
            {id: 2, annotation: {filtered: [{HGVSc: "NM_007294.3:c.4535-200G>T"}, {HGVSc: "NM_007294.3:c.4535-213G>T"}]}}
        ];

        let res = service.filterIntronicAlleles(someAlleles);
        expect(res.length).toEqual(2);

    })
});

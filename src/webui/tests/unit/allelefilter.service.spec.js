import AlleleFilter from '../../src/js/services/alleleFilter.service.js'

describe('AlleleFilter service', function() {
    /**
     * return an object having a getConfig function. The function returns an object with frequency cutoffs
     * See config.py
     */
    function makeConfig(freq, signed_cutoffs) {
        var mockConfig = function() {}
        mockConfig.getConfig = function() {
            return {
                frequencies: { criterias: freq },
                variant_criteria: {
                    intronic_region: signed_cutoffs
                }
            }
        }
        return mockConfig
    }

    it('can be constructed', function() {
        expect(new AlleleFilter(makeConfig({ someKey: 12 }))).toBeDefined()
    })
})

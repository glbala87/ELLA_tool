describe('filter', function() {
    var $filter

    describe('noUnderscores', function() {
        var f

        beforeEach(function() {
            angular.mock.module('workbench')
            inject(function(_$filter_) {
                f = _$filter_('noUnderscores')
            })
        })

        it('replaces _ with space', function() {
            expect(f('abc_def')).toEqual('abc def')
        })

        it('returns empty string for undefined', function() {
            expect(f(undefined)).toEqual('')
        })
    })
})

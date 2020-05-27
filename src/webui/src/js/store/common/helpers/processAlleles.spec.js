import processAlleles from './processAlleles'

const BASEALLELE = {
    change_type: 'SNP',
    chromosome: '15',
    start_position: 123,
    open_end_position: 124,
    change_from: 'A',
    change_to: 'G',
    annotation: {
        filtered_transcripts: [],
        transcripts: [],
        frequencies: {},
        external: {}
    }
}

describe('properly formats allelesformattedAlleles', function() {
    it('simple SNP', function() {
        expect(
            processAlleles([
                Object.assign(BASEALLELE, {
                    change_type: 'SNP',
                    chromosome: '15',
                    start_position: 123,
                    open_end_position: 124,
                    change_from: 'A',
                    change_to: 'G'
                })
            ])
        ).toMatchObject([
            {
                formatted: {
                    genomicPosition: '15:124',
                    hgvsg: 'g.124A>G'
                }
            }
        ])
    })

    it('1 base deletion', () => {
        expect(
            processAlleles([
                Object.assign(BASEALLELE, {
                    change_type: 'del',
                    chromosome: '15',
                    start_position: 123,
                    open_end_position: 124,
                    change_from: 'A',
                    change_to: ''
                })
            ])
        ).toMatchObject([
            {
                formatted: {
                    genomicPosition: '15:124',
                    hgvsg: 'g.124del'
                }
            }
        ])
    })

    it('3 base deletion', () => {
        expect(
            processAlleles([
                Object.assign(BASEALLELE, {
                    change_type: 'del',
                    chromosome: '15',
                    start_position: 123,
                    open_end_position: 126,
                    change_from: 'AGC',
                    change_to: ''
                })
            ])
        ).toMatchObject([
            {
                formatted: {
                    genomicPosition: '15:124-126',
                    hgvsg: 'g.124_126del'
                }
            }
        ])
    })

    it('1 base insertion', () => {
        expect(
            processAlleles([
                Object.assign(BASEALLELE, {
                    change_type: 'ins',
                    chromosome: '15',
                    start_position: 123,
                    open_end_position: 124,
                    change_from: '',
                    change_to: 'T'
                })
            ])
        ).toMatchObject([
            {
                formatted: {
                    genomicPosition: '15:124-125',
                    hgvsg: 'g.124_125insT'
                }
            }
        ])
    })

    it('3 base insertion', () => {
        expect(
            processAlleles([
                Object.assign(BASEALLELE, {
                    change_type: 'ins',
                    chromosome: '15',
                    start_position: 123,
                    open_end_position: 124,
                    change_from: '',
                    change_to: 'TTT'
                })
            ])
        ).toMatchObject([
            {
                formatted: {
                    genomicPosition: '15:124-125',
                    hgvsg: 'g.124_125insTTT'
                }
            }
        ])
    })

    it('2 bases deleted, 1 inserted', () => {
        expect(
            processAlleles([
                Object.assign(BASEALLELE, {
                    change_type: 'indel',
                    chromosome: '15',
                    start_position: 123,
                    open_end_position: 125,
                    change_from: 'AA',
                    change_to: 'T'
                })
            ])
        ).toMatchObject([
            {
                formatted: {
                    genomicPosition: '15:124-125',
                    hgvsg: 'g.124_125delinsT'
                }
            }
        ])
    })
    it('1 base deleted, 3 inserted', () => {
        expect(
            processAlleles([
                Object.assign(BASEALLELE, {
                    change_type: 'indel',
                    chromosome: '15',
                    start_position: 123,
                    open_end_position: 124,
                    change_from: 'A',
                    change_to: 'TTT'
                })
            ])
        ).toMatchObject([
            {
                formatted: {
                    genomicPosition: '15:124',
                    hgvsg: 'g.124delinsTTT'
                }
            }
        ])
    })
})

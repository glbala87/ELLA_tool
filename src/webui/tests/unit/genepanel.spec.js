import Genepanel from '../../src/js/model/genepanel'

const genepanel_defaults = {
    'disease_mode': "ANY",
    'inheritance': "AD",
    'last_exon': true,
    'freq_cutoffs': {
        'AD': {
            'hi_freq_cutoff': 0.0005,
            'lo_freq_cutoff': 0.0001
        },
        'Other': {
            'hi_freq_cutoff': 0.01,
            'lo_freq_cutoff': 1
        }
    }
};

describe("Model Genepanel", function() {

    function createPanel(includeConfig) {
        let config = {
            'data': {
                'BRCA1': {'inheritance': 'XX', 'last_exon': false, 'hi_freq_cutoff': 0.001},
                'BRCA3': {'inheritance': 'XX'}

            }
        };

        let genepanel = {
            'phenotypes': [
                {'gene': {'hugoSymbol': 'BRCA1'}, 'inheritance': 'AD'},
                {'gene': {'hugoSymbol': 'BRCA2'}, 'inheritance': 'AR', 'description': "a phenotype"},
                {'gene': {'hugoSymbol': 'BRCA1'}, 'inheritance': 'AD'},
                {'gene': {'hugoSymbol': 'BRCA1'}, 'inheritance': ''}
            ]
        };

        if (includeConfig) {
            genepanel['config'] = config;
        }
        return genepanel;
    }

    it("can be constructed", function () {
        expect(new Genepanel({'id': 12})).toBeDefined();
    });

    it("can find inheritance from phenotypes", function () {
        expect(new Genepanel(createPanel(false)).getInheritanceCodes('BRCA1')).toBe('AD');
    });

    it("can filter phenotypes by gene symbol", function () {
        let phenotypes = new Genepanel(createPanel(false)).phenotypesBy('BRCA2');
        expect(phenotypes[0]['description']).toBe('a phenotype');
    });

    it("handles missing genepanel config", function () {
        let gene_override = false;
        let data = {'id': 1, 'genepanel': createPanel(gene_override)};
        let overrides = new Genepanel(createPanel(false)).findGeneConfigOverrides('BRCA1');
        expect(overrides).toBeDefined();
    });

    it("can find inheritance from genepanel config", function () {
        expect(new Genepanel(createPanel(true)).getInheritanceCodes('BRCA1')).toBe('XX');
    });

    it("can find genepanel config overrides for last_exon and inheritance", function() {

        let genepanelConfig_brca1 = new Genepanel(createPanel(true)).calculateGenepanelConfig('BRCA1', genepanel_defaults);
        expect(typeof genepanelConfig_brca1['inheritance']).toBe('string'); // now wrapper for inheritance
        expect(genepanelConfig_brca1['inheritance']).toBe('XX');
        expect(typeof genepanelConfig_brca1['last_exon']).toBe('object');
        expect(genepanelConfig_brca1['last_exon']['value']).toBe(false);

        let genepanelConfig_brca3 = new Genepanel(createPanel(true)).calculateGenepanelConfig('BRCA3', genepanel_defaults);
        expect(genepanelConfig_brca3['last_exon']).toBe(true);
    });

    it("can find genepanel config overrides for frequence cutoffs", function () {

        let genepanelConfig_brca1 = new Genepanel(createPanel(true)).calculateGenepanelConfig('BRCA1', genepanel_defaults);
        expect(typeof genepanelConfig_brca1['hi_freq_cutoff']).toBe('object');
        expect(genepanelConfig_brca1['hi_freq_cutoff']['value']).toBe(0.001);

        expect(typeof genepanelConfig_brca1['lo_freq_cutoff']).toBe('number');
        expect(genepanelConfig_brca1['lo_freq_cutoff']).toBe(1); // default for 'Other'

    })



});

/* jshint esnext: true */

export default class Analysis {
    /**
     * Represents one Analysis.
     * 
     * Also holds the genepanel (which should be model.Genepanel in the future)
     * @param  {object} Analysis data from server, see api/v1/interpretations/
     */
    constructor(data) {
        console.log('Constructor for Analysis with id=' + data.id);
        Object.assign(this, data);

    }

    getInterpretationState() {
        var STATE_PRIORITY = ['Not started', 'Ongoing', 'Done'];
        let states = this.interpretations.map(x => x.status);
        if (states.length) {
            return states.sort(x => STATE_PRIORITY.indexOf(x))[0];
        }
    }

    findGeneConfig(geneSymbol) {
        let panelConfig = this.genepanel.config;
        if (panelConfig && panelConfig.data && geneSymbol in panelConfig.data) {
            return panelConfig.data[geneSymbol];
        }
    }

    // a dict whose keys are the possible properties of a genepanel and the value
    // is either a primitive or an object. The latter of form {'_type': 'genepanel_override', value: primitive}
    calculateGenepanelConfig(geneSymbol, default_genepanel_config) {
        let result = {};
        let props = ['last_exon', 'disease_mode']; // see api/util/genepanelconfig.py#COMMON_GENEPANEL_CONFIG
        let overrides = this.findGeneConfig(geneSymbol);
        for (let p of props) {
                result[p] = p in overrides ?
                    {'_type': 'genepanel_override', 'value': overrides[p]} : default_genepanel_config[p];
        }

        result['inheritance'] = this.getInheritanceCodes(geneSymbol); // no object wrapper
        // TODO: look deeper into struct to find cutoffs

        console.log(result);
        return result;
    }

    getInheritanceCodes(geneSymbol) {
        if (! this.genepanel) {
            return '';
        }

        let source = this.genepanel.phenotypes;
        let config = this.findGeneConfig(geneSymbol);
        if (config && 'inheritance' in config) {
            return config['inheritance'];
        }

        if (source) {
            let codes = source.filter(ph => ph.gene.hugoSymbol == geneSymbol)
                .map( ph => ph.inheritance)
                .filter(i => i) // remove empty
                .sort();

            return codes.join('/');
        } else {
            return '';
        }

    }

    
    getInterpretationId() {
        // TODO: implement me
        return this.interpretations[this.interpretations.length - 1].id;
    }

    /**
     * Returns the user of the last interpretation for analysis.
     */
    getInterpretationUser() {
        return this.interpretations[this.interpretations.length - 1].user;
    }
}



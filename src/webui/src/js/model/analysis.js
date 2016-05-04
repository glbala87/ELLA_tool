/* jshint esnext: true */

export default class Analysis {
    /**
     * Represents one Analysis.
     * 
     * Also holds the genepanel (which should be model.Genepanel in the future)
     * @param  {object} Analysis data from server.
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
    getInheritanceCodes(geneSymbol) {
        if (! this.genepanel) {
            return '';
        }

        let source = this.genepanel.phenotypes;

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



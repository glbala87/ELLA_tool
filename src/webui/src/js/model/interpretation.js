/* jshint esnext: true */

class Interpretation {
    /**
     * Represents one Analysis.
     * @param  {object} Analysis data from server.
     */
    constructor(data) {
        console.log(data);
        this.id = data.id;
        this.status = data.status;
        this.analysis = data.analysis;
        this.dateLastUpdate = data.dateLastUpdate;
        this.setAlleles(data.alleles);
        this.state = data.guiState;

        this.dirty = false; // Indicates whether the Interpretation has been modified

    }

    setAlleles(alleles) {
        this.alleles = [];
        for (let allele of alleles) {
            this.alleles.push(new Allele(allele));
        }
    }


}

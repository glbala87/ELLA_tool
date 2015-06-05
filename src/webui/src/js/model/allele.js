/* jshint esnext: true */

class Allele {
    /**
     * Represents one Allele (aka variant)
     * @param  {object} Allele data from server.
     */
    constructor(data) {
        Object.assign(this, data);
        this._data = data;
        this.annotation = this._createAnnotations();
        this.annotation_transcript = null;
    }

    setAnnotationTranscript(transcripts) {
        this.annotation_transcript = this.annotation.getByTranscripts(transcripts);
    }

    _createAnnotations() {
        return new Annotation(this._data.annotation.annotations);
    }

    getTranscripts() {
        return this.annotation.transcripts.map(x => x.transcript);
    }

    getReferenceData() {
        return this.annotation_transcript.getReferenceData();
    }

}

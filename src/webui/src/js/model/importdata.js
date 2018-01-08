/* jshint esnext: true */

export class ImportData {

    constructor(filename, input) {
        this.filename = filename;
        this.input = input;

        this.contents = {
            lines: {}, // {displayValue: {value: line, include: true/false}, ...}
            header: "",
        };

        this._choices = {
            mode: ["Analysis", "Variants"],
            type: ["Create", "Append"],
            technology: ["Sanger", "HTS"]
        }

        // Current import selection, with validation of choices
        this.importSelection = {
            _choices: this._choices,
            // Mode
            _mode: this._choices.mode[0],
            get mode() {
                return this._mode;
            },
            set mode(val) {
                if (this._choices["mode"].indexOf(val) < 0) {
                    console.error(`Invalid choice for mode: ${val}`);
                    return;
                }
                this._mode = val;
            },
            // Type
            _type: this._choices.type[0],
            get type() {
                return this._type;
            },
            set type(val) {
                if (this._choices["type"].indexOf(val) < 0) {
                    console.error(`Invalid choice for type: ${val}`);
                    return;
                }
                this._type = val;
            },
            // Technology
            _technology: this._choices.technology[0],
            get technology() {
                return this._technology;
            },
            set technology(val) {
                if (this._choices["technology"].indexOf(val) < 0) {
                    console.error(`Invalid choice for technology: ${val}`);
                    return;
                }
                this._technology = val;
            },
            // Non-validated choices
            analysis: null,
            analysisName: "",
            genepanel: null,
        }

        //
        this._hasGenotype = true;

        this.parse()
    }

    getChoices(key) {
        return this._choices[key];
    }

    analysisMode() {
        return this.importSelection.mode === "Analysis"
    }

    createNewAnalysisType() {
        return this.analysisMode() && this.importSelection.type === "Create";
    }

    appendToAnalysisType() {
        return this.analysisMode() && this.importSelection.type === "Append";
    }

    variantMode() {
        return this.importSelection.mode === "Variants";
    }

    // Contents
    parse() {
        let lines = this.input.trim().split('\n');
        let header = ""
        let fileType;
        for (let l of lines) {
            if (l.trim() === "") {
                continue;
            }
            if (l.trim().startsWith("#CHROM")) {
                fileType = "vcf"
            } else if (l.trim().startsWith("Index")) {
                fileType = "seqpilot";
            }

            if (l.trim().startsWith("#") || l.trim().startsWith("Index")) {
                header += l +"\n"
                continue;
            }
            let key;
            if (fileType === "vcf") {
                key = this._parseVcfLine(l)
            } else if (fileType === "seqpilot") {
                key = this._parseSeqPilotLine(l)
            } else {
                key = this._parseGenomicOrHGVScLine(l);
            }

            this.contents.lines[key] = {
                value: l,
                include: true,
            }
        }

        this.contents.header = header.trim();
    }

    _parseVcfLine(line) {
        let vals = line.trim().split("\t")
        let chrom = vals[0];
        let pos = vals[1];
        let ref = vals[3];
        let alt = vals[4];

        let format = vals[8];
        let sample = vals[9];

        let genotype;
        let gt_index = format.split(':').indexOf("GT");
        if (gt_index < 0) {
            genotype = "?/?"
            this._hasGenotype = false;
        } else {
            genotype = sample.split(':')[gt_index];
        }

        return `${chrom}:${pos} ${ref}>${alt} (${genotype})`
    }

    _parseSeqPilotLine(line) {
        let vals = line.trim().split("\t");
        let transcript = vals[2];
        let cdna = vals[11];
        let genotype = vals[6].match(/\(het\)|\(hom\)/);
        if (!genotype) {
            this._hasGenotype = false;
            genotype = "(?)"
        }

        return `${transcript}.${cdna} ${genotype}`
    }

    _parseGenomicOrHGVScLine(line) {
        let genotype = line.match(/ \((het|hom)\)?/)
        if (!genotype) {
            this._hasGenotype = false;
        }
        return line
    }

    genotypeAvailable() {
        return this._hasGenotype
    }

    getFileNameBase() {
        let fileNameBase = "";
        if (this.filename) {
            if (this.filename.contains('.')) {
                fileNameBase = this.filename.substring(0, this.filename.lastIndexOf('.'));
            } else {
                fileNameBase = this.filename;
            }
        }
        return fileNameBase;
    }

    getFilename() {
        return this.filename;
    }

    _rebuildData() {
        let data = this.contents.header;
        for (let ld of Object.values(this.contents.lines)) {
            if (ld.include) {
                data += "\n"+ld.value;
            }
        }
        return data
    }

    // Import selection
    isSelectionComplete() {
        let a = this.importSelection.mode === "Variants" && this.importSelection.genepanel;
        let b = this.importSelection.mode === "Analysis" && this.importSelection.type === "Create" && this.importSelection.analysisName && this.importSelection.genepanel;
        let c = this.importSelection.mode === "Analysis" && this.importSelection.type === "Append" && this.importSelection.analysis;
        let d = Object.values(this.contents.lines).filter(c => c.include).length

        return Boolean((a || b || c) && d);
    }

    process() {

        let properties = {
            sample_type: this.importSelection.technology,
        }

        if (this.importSelection.mode === "Analysis") {
            properties.create_or_append = this.importSelection.type;
            properties.analysis_name = this.importSelection.type === "Append" ? this.importSelection.analysis.name : this.importSelection.analysisName;
        }

        let data = {
            mode: this.importSelection.mode,
            data: this._rebuildData(),
            genepanel_name: this.importSelection.genepanel.name,
            genepanel_version: this.importSelection.genepanel.version,
            properties: properties,
        }

        return data;
    }



}



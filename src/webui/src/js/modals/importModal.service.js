'use strict';
import {Service, Inject} from '../ng-decorators';
import {UUID} from '../util';

export class ImportController {
    constructor(modalInstance, User, AnalysisResource, AnnotationjobResource, toastr, $interval, $filter,$scope) {
        this.modal = modalInstance;
        this.user = User.getCurrentUser();
        this.analysisResource = AnalysisResource;
        this.annotationjobResource = AnnotationjobResource;
        this.toastr = toastr;
        this.filter = $filter;

        this.modes = ["Parse file", "Manual"];
        this.mode = this.modes[0];

        this.types = ["Create", "Append"];
        this.type = this.types[0];
        this.analyses = [];
        this.jobData = null;

        this.reset()

        $scope.$watch(
            () => User.getCurrentUser(),
            () => {
                this.user = User.getCurrentUser()
            }
        )


        this.interval = $interval;
        this.scope = $scope

        this.scope.$watch(
            () => this.mode,
            () => {this.reset()}
        )

        // DEBUG
        // this.mode = this.modes[1];
        // this.parseVCF()
        this.annotationjobResource.annotationServiceRunning().then((isAlive) => {
            if (!isAlive) {
                this.toastr.error("Unable to connect to annotation service. Start the annotation service and try again", 10000);
            }
        });
        this.getAnnotationjobs();
        this.pollForAnnotationJobs();

    }

    reset() {
        this.description = "";
        this.genepanel = null;
        this.analysis_name = "";
        this.selected_analysis = "";
        this.sample_type = "Sanger";

        this.parsed_vcf = '';
        this.input_data = '';

        this.rawInput = '';
        this.rawInput = `------------- brca_sample_master.vcf
##fileformat=VCFv4.1
##contig=<ID=13>
##FILTER=<ID=PASS,Description="All filters passed">
#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO	FORMAT	brca_sample_master
1	32893243	CM067653	G	T	5000.0	PASS	.	GT:AD:DP:GQ:PL	0/1:107,80:187:99:2048,0,2917
13	32893243	CM067653	G	T	5000.0	PASS	.	GT:AD:DP:GQ:PL	0/1:107,80:187:99:2048,0,2917
13	32893435	CM062477	G	T	5000.0	PASS	.	GT:AD:DP:GQ:PL	0/1:107,80:187:99:2048,0,2917
13	32900290	CS994297	A	G	5000.0	PASS	.	GT:AD:DP:GQ:PL	0/1:107,80:187:99:2048,0,2917
13	32900700	CM960192	G	A	5000.0	PASS	.	GT:AD:DP:GQ:PL	0/1:107,80:187:99:2048,0,2917
13	32905054	CS144707	A	C	5000.0	PASS	.	GT:AD:DP:GQ:PL	0/1:107,80:187:99:2048,0,2917
13	32906535	CI1111183	G	GT	5000.0	PASS	.	GT:AD:DP:GQ:PL	0/1:107,80:187:99:2048,0,2917
13	32906847	CI101425	T	TA	5000.0	PASS	.	GT:AD:DP:GQ:PL	0/1:107,80:187:99:2048,0,2917
13	32907058	CD114478	TC	T	5000.0	PASS	.	GT:AD:DP:GQ:PL	0/1:107,80:187:99:2048,0,2917
-------------seqpilot_export.csv
Index	Gene	Transcript	Location	Pos.	Type	Nuc Change	AA Change	State	Hint	web Ref.	c. HGVS	p. HGVS	mut Entry	mut Effect
6	MSH2	NM_000251.2	E5	5 (797) / 4bp   [chr2:g.47641411_47641412 (hg19)]	I	AAGA (het)	[STOP] AA 284 (E5/58)	S	RF changed		c.796_797insAAGA	p.Ala266Glufs*19	0/1 of 1963
4	BRCA2	NM_000059.3	E18	188 (8164) / 4bp   [chr13:g.32937502_32937503 (hg19)]	I	GCTC (het)	[STOP] AA 2730 (E18/212)	S	RF changed		c.8163_8164insGCTC	p.Thr2722Alafs*9	0/1 of 6244
6	BRCA2	NM_000059.3	E27	85 (9733) / 1bp   [chr13:g.32972382_32972383 (hg19)]	I	A (het)	[STOP] AA 3254 (E27/112)	S	RF changed		c.9732_9733insA	p.Ser3245Ilefs*10	0/1 of 6200
1	VHL	NM_000551.3	E3	39 (502) / 8bp   [chr3:g.10191508_10191509 (hg19)]	I	TTGTCCGT (het)	[STOP] AA 172 (E3/51)	SV	RF 		c.501_502insTTGTCCGT	p.Ser168Leufs*5	0/1 of 74
1	BRCA1	NM_007294.3	E8	17 (458) / 21bp   [chr17:g.41251881_41251882 (hg19)]	I	ATTACCAGGAAACCAGTCTCA (het)	S -> NYQETSLS (153)	SV			c.457_458insATTACCAGGAAACCAGTCTCA	p.Ser153delinsAsnTyrGlnGluThrSerLeuSer	0/1 of 6177
5	BRCA2	NM_000059.3	E19	-7 / 1bp   [chr13:g.32944532 (hg19)]	D	t (het)		S			c.8332-7delT		0/1 of 6129
1	BRCA1	NM_007294.3	E3	-11 / 1bp   [chr17:g.41267807 (hg19)]	D	t (het)		SV			c.81-11delT		0/1 of 6171
1	VHL	NM_000551.3	E3	39 (502) / 8bp   [chr3:g.10191508_10191509 (hg19)]	I	TTGTCCGT (het)	[STOP] AA 172 (E3/51)	SV	RF changed		c.501_502insTTGTCCGT	p.Ser168Leufs*5	0/1 of 80		alex [02/02/2016 13:18:48]	yngs [02/03/2016 09:47:46]
5	BRCA2	NM_000059.3	E6	11..13 (486..488) / 3bp   [chr13:g.32900389_32900391 (hg19)]	D	GAG (het)	GS -> G (162..163)	S			c.486_488delGAG	p.Gly162_Ser163delinsGly	0/3 of 6794 (p.Ser163del)			vibw [11/07/2016 12:39:37]`


//         this.rawInput = `##fileformat=VCFv4.1
// ##contig=<ID=13>
// ##FILTER=<ID=PASS,Description="All filters passed">
// #CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO	FORMAT	brca_sample_master
// 1	32893243	CM067653	G	T	5000.0	PASS	.	GT:AD:DP:GQ:PL	0/1:107,80:187:99:2048,0,2917
// 13	32893243	CM067653	G	T	5000.0	PASS	.	GT:AD:DP:GQ:PL	0/1:107,80:187:99:2048,0,2917
// 13	32893435	CM062477	G	T	5000.0	PASS	.	GT:AD:DP:GQ:PL	0/1:107,80:187:99:2048,0,2917
// 13	32900290	CS994297	A	G	5000.0	PASS	.	GT:AD:DP:GQ:PL	0/1:107,80:187:99:2048,0,2917
// 13	32900700	CM960192	G	A	5000.0	PASS	.	GT:AD:DP:GQ:PL	0/1:107,80:187:99:2048,0,2917
// 13	32905054	CS144707	A	C	5000.0	PASS	.	GT:AD:DP:GQ:PL	0/1:107,80:187:99:2048,0,2917
// 13	32906535	CI1111183	G	GT	5000.0	PASS	.	GT:AD:DP:GQ:PL	0/1:107,80:187:99:2048,0,2917
// 13	32906847	CI101425	T	TA	5000.0	PASS	.	GT:AD:DP:GQ:PL	0/1:107,80:187:99:2048,0,2917
// 13	32907058	CD114478	TC	T	5000.0	PASS	.	GT:AD:DP:GQ:PL	0/1:107,80:187:99:2048,0,2917`

        this.parsedInput = null;

        this.parsed_variants = [];
        this.header = "";

        // Single variant
        //13	32890607	SNP	G	T	5000.0	PASS	.	GT:AD:DP:GQ:PL	0/1:107,80:187:99:2048,0,2917
        this.chromosome = '';
        this.position = '';
        this.ref = '';
        this.alt = '';

    }

    pollForAnnotationJobs() {
        let cancel = this.interval(() => this.getAnnotationjobs(), 5000);
        this.scope.$on('$destroy', () => this.interval.cancel(cancel));
    }

    getAnnotationjobs() {
        let popups_open = document.getElementsByClassName("annotationjobinfo").length > 0;
        if (!popups_open) {
            this.annotationjobResource.get().then((res) => {
                this.annotationjobs = res;
            })
        }
    }

    deleteJob(id) {
        this.annotationjobResource.delete(id);
    }

    restartJob(id) {
        this.annotationjobResource.restart(id);
    }

    parseInput() {
        let parsedInput = {}
        let jobData = {}

        // Find lines starting with '-'
        let lines = this.rawInput.split("\n");
        let currentFile = "";
        let uuid = null;
        for (let l of lines) {
            if (l.trim() == "") continue;

            // Check if start of new file
            if (!uuid || l.startsWith('-')) {
                uuid = UUID()
                if (l.startsWith('-')) {
                    currentFile = l.replace(/-*\s*/g, '')
                } else {
                    currentFile = '';
                }

                parsedInput[uuid] = {
                    filename: currentFile,
                    fileContents: '',
                }

                // Job data will be populated in importsingle
                jobData[uuid] = {
                    mode: null,
                    type: null,
                    genepanel: null,
                    analysis: null,
                    analysisName: "",
                    technology: null,
                    selectionComplete: false,
                    user_id: this.user.id,
                };

                // Don't include line in contents if it is a separator line
                if (l.startsWith('-')) continue;

            }

            parsedInput[uuid].fileContents += l+"\n";
        }

        this.parsedInput = parsedInput;
        this.jobData = jobData;
    }

    getImportDescription() {
        let incomplete = 0;
        let createAnalyses = 0;
        let standaloneVariants = 0;
        let appendAnalyses = [];
        let appendVariants = 0;

        for (let j of Object.values(this.jobData)) {
            if (!j.selectionComplete) {
                incomplete += 1;
            } else if (j.type === "Analysis") {
                if (j.mode === "Create") {
                    createAnalyses += 1;
                } else if (j.mode === "Append") {
                    appendAnalyses.push(j.analysis.name);
                    appendVariants += Object.values(j.contentLines).filter(l => l.include).length;
                }
            }
        }

        appendAnalyses = new Set(appendAnalyses).size;

        let description = [];
        if (incomplete) {
            let s = `${incomplete} ${incomplete > 1 ? "imports" : "import"} incomplete.`;
            description.push(s);
        }

        if (createAnalyses) {
            let s = `Create ${createAnalyses} new ${createAnalyses > 1 ? "analyses" : "analysis"}.`;
            description.push(s);
        }

        if (appendAnalyses) {
            let s = `Append ${appendVariants} ${appendVariants > 1 ? "variants": "variant"} to ${appendAnalyses} existing ${appendAnalyses > 1 ? "analyses" : "analysis"}`;
            description.push(s);
        }

        if (standaloneVariants) {
            let s = `Import ${standaloneVariants} standalone ${standaloneVariants > 1 ? "variants" : "variant"}`;
            description.push(s);
        }

        return description;
    }



    rebuildFile(header, contentLines) {
        let data = header;
        for (let ld of Object.values(contentLines)) {
            if (ld.include) {
                data += "\n"+ld.contents;
            }
        }
        return data
    }

    import() {
        let processedJobData = {}
        for (let id in this.jobData) {
            let jobdata = this.jobData[id];
            let rebuilt = this.rebuildFile(jobdata.header, jobdata.contentLines)

            let properties = {
                sample_type: jobdata.technology,
            }

            if (jobdata.type === "Analysis") {
                properties.create_or_append = jobdata.mode;
                properties.analysis_name = jobdata.mode === "Append" ? jobdata.analysis.name : jobdata.analysisName;
            }

            processedJobData[id] = {
                data: rebuilt,
                mode: jobdata.type,
                genepanel_name: jobdata.genepanel.name,
                genepanel_version: jobdata.genepanel.version,
                properties: properties,
                user_id: this.user.id,
            }

        }


        this.modal.close(processedJobData)

    }

    importDisabled() {
        let allReady = Object.values(this.jobData).map(j => j.selectionComplete).every(v => v);
        return !allReady;
    }
}

@Service({
    serviceName: 'ImportModal'
})

@Inject('$uibModal', '$resource', 'User', "AnnotationjobResource")
export class ImportModal {

    constructor($uibModal, $resource, User, AnnotationjobResource) {
        this.modalService = $uibModal;
        this.resource = $resource;
        this.base = '/api/v1/';
        this.user = User;
        this.annotationjobResource = AnnotationjobResource;
    }

    show() {

        let modal = this.modalService.open({
            templateUrl: 'ngtmpl/importModal.ngtmpl.html',
            controller: [
                '$uibModalInstance',
                'User',
                "AnalysisResource",
                "AnnotationjobResource",
                "toastr",
                "$interval",
                "$filter",
                "$scope",
                ImportController
            ],
            controllerAs: 'vm',
            size: 'lg',
            backdrop: 'static',
        });

        return modal.result.then((result) => {
            if (result) {
                let promises = []
                for (let k in result) {
                    promises.push(this.annotationjobResource.post(result[k]))
                }
                return Promise.all(promises)
            }
        });
    }
}

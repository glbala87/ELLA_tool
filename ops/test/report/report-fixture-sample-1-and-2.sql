--
-- Created by performing manual classification on brca_e2e_test01.HBOC_v01,
-- then selecting relevant parts from a pg_dump
-- To see what's been done, load into db and check the UI.
--

DELETE FROM public.analysisinterpretationsnapshot;
DELETE FROM public.allelereport;
DELETE FROM public.alleleassessment;
DELETE FROM public.interpretationstatehistory;
DELETE FROM public.analysisinterpretation;

COPY public.alleleassessment (id, classification, evaluation, user_id, date_created, date_superceeded, previous_assessment_id, allele_id, genepanel_name, genepanel_version, analysis_id, annotation_id, custom_annotation_id) FROM stdin;
1	1	{"acmg": {"included": [], "suggested": [{"op": "$in", "code": "REQ_GP_AD", "match": ["AD"], "source": "genepanel.inheritance"}, {"op": "$in", "code": "REQ_GP_last_exon_not_important", "match": ["LENI"], "source": "genepanel.last_exon_important"}, {"op": "$in", "code": "REQ_GP_LOF_missense", "match": ["ANY"], "source": "genepanel.disease_mode"}, {"op": "$in", "code": "REQ_not_in_last_exon", "match": ["no"], "source": "transcript.in_last_exon"}, {"op": "$in", "code": "REQ_null_variant", "match": ["stop_gained"], "source": "transcript.consequences"}, {"op": "$in", "code": "REQ_no_freq", "match": ["null_freq"], "source": "frequencies.commonness"}, {"op": null, "code": "PVS1", "match": null, "source": null}, {"op": null, "code": "PPxPM2", "match": null, "source": null}], "suggested_classification": null}, "external": {"comment": ""}, "frequency": {"comment": ""}, "reference": {"comment": ""}, "prediction": {"comment": ""}, "classification": {"comment": ""}}	1	2018-08-08 08:49:40.471413+00	\N	\N	1	HBOC	v01	1	9	1
2	2	{"acmg": {"included": [], "suggested": [{"op": "$in", "code": "REQ_GP_AD", "match": ["AD"], "source": "genepanel.inheritance"}, {"op": "$in", "code": "REQ_GP_last_exon_not_important", "match": ["LENI"], "source": "genepanel.last_exon_important"}, {"op": "$in", "code": "REQ_GP_LOF_missense", "match": ["ANY"], "source": "genepanel.disease_mode"}, {"op": "$in", "code": "REQ_not_in_last_exon", "match": ["no"], "source": "transcript.in_last_exon"}, {"op": "$in", "code": "REQ_no_freq", "match": ["null_freq"], "source": "frequencies.commonness"}, {"op": null, "code": "PPxPM2", "match": null, "source": null}], "suggested_classification": null}, "external": {"comment": ""}, "frequency": {"comment": ""}, "reference": {"comment": ""}, "prediction": {"comment": ""}, "classification": {"comment": ""}}	1	2018-08-08 08:49:40.47496+00	\N	\N	2	HBOC	v01	1	10	\N
3	3	{"acmg": {"included": [], "suggested": [{"op": "$in", "code": "REQ_GP_AD", "match": ["AD"], "source": "genepanel.inheritance"}, {"op": "$in", "code": "REQ_GP_last_exon_not_important", "match": ["LENI"], "source": "genepanel.last_exon_important"}, {"op": "$in", "code": "REQ_GP_LOF_missense", "match": ["ANY"], "source": "genepanel.disease_mode"}, {"op": "$in", "code": "REQ_not_in_last_exon", "match": ["no"], "source": "transcript.in_last_exon"}, {"op": "$in", "code": "REQ_null_variant", "match": ["stop_gained"], "source": "transcript.consequences"}, {"op": "$in", "code": "REQ_no_freq", "match": ["null_freq"], "source": "frequencies.commonness"}, {"op": null, "code": "PVS1", "match": null, "source": null}, {"op": null, "code": "PPxPM2", "match": null, "source": null}], "suggested_classification": null}, "external": {"comment": ""}, "frequency": {"comment": ""}, "reference": {"comment": ""}, "prediction": {"comment": ""}, "classification": {"comment": ""}}	1	2018-08-08 08:49:40.47616+00	\N	\N	3	HBOC	v01	1	11	\N
4	4	{"acmg": {"included": [], "suggested": [{"op": "$in", "code": "REQ_GP_AD", "match": ["AD"], "source": "genepanel.inheritance"}, {"op": "$in", "code": "REQ_GP_last_exon_not_important", "match": ["LENI"], "source": "genepanel.last_exon_important"}, {"op": "$in", "code": "REQ_GP_LOF_missense", "match": ["ANY"], "source": "genepanel.disease_mode"}, {"op": "$in", "code": "REQ_not_in_last_exon", "match": ["no"], "source": "transcript.in_last_exon"}, {"op": "$in", "code": "REQ_null_variant", "match": ["frameshift_variant"], "source": "transcript.consequences"}, {"op": "$in", "code": "REQ_no_freq", "match": ["null_freq"], "source": "frequencies.commonness"}, {"op": null, "code": "PVS1", "match": null, "source": null}, {"op": null, "code": "PPxPM2", "match": null, "source": null}], "suggested_classification": null}, "external": {"comment": ""}, "frequency": {"comment": ""}, "reference": {"comment": ""}, "prediction": {"comment": ""}, "classification": {"comment": ""}}	1	2018-08-08 08:49:40.477307+00	\N	\N	4	HBOC	v01	1	4	\N
5	5	{"acmg": {"included": [], "suggested": [{"op": "$in", "code": "REQ_GP_AD", "match": ["AD"], "source": "genepanel.inheritance"}, {"op": "$in", "code": "REQ_GP_last_exon_not_important", "match": ["LENI"], "source": "genepanel.last_exon_important"}, {"op": "$in", "code": "REQ_GP_LOF_missense", "match": ["ANY"], "source": "genepanel.disease_mode"}, {"op": "$in", "code": "REQ_not_in_last_exon", "match": ["no"], "source": "transcript.in_last_exon"}, {"op": "$in", "code": "REQ_null_variant", "match": ["frameshift_variant"], "source": "transcript.consequences"}, {"op": "$in", "code": "REQ_no_freq", "match": ["null_freq"], "source": "frequencies.commonness"}, {"op": null, "code": "PVS1", "match": null, "source": null}, {"op": null, "code": "PPxPM2", "match": null, "source": null}], "suggested_classification": null}, "external": {"comment": ""}, "frequency": {"comment": ""}, "reference": {"comment": ""}, "prediction": {"comment": ""}, "classification": {"comment": ""}}	1	2018-08-08 08:49:40.478405+00	\N	\N	5	HBOC	v01	1	5	\N
6	1	{"acmg": {"included": [], "suggested": [{"op": "$in", "code": "REQ_GP_last_exon_important", "match": ["LEI"], "source": "genepanel.last_exon_important"}, {"op": "$in", "code": "REQ_GP_LOF_missense", "match": ["ANY"], "source": "genepanel.disease_mode"}, {"op": "$in", "code": "REQ_not_in_last_exon", "match": ["no"], "source": "transcript.in_last_exon"}, {"op": "$in", "code": "REQ_null_variant", "match": ["stop_gained"], "source": "transcript.consequences"}, {"op": "$in", "code": "REQ_no_freq", "match": ["null_freq"], "source": "frequencies.commonness"}, {"op": null, "code": "PVS1", "match": null, "source": null}, {"op": null, "code": "PPxPM2", "match": null, "source": null}], "suggested_classification": null}, "external": {"comment": ""}, "frequency": {"comment": ""}, "reference": {"comment": ""}, "prediction": {"comment": ""}, "classification": {"comment": ""}}	1	2018-08-08 08:55:54.878047+00	\N	\N	7	HBOCUTV	v01	2	12	\N
7	2	{"acmg": {"included": [], "suggested": [{"op": "$in", "code": "REQ_GP_last_exon_important", "match": ["LEI"], "source": "genepanel.last_exon_important"}, {"op": "$in", "code": "REQ_GP_LOF_missense", "match": ["ANY"], "source": "genepanel.disease_mode"}, {"op": "$in", "code": "REQ_no_aa_change", "match": ["synonymous_variant"], "source": "transcript.consequences"}, {"op": "$in", "code": "REQ_not_in_last_exon", "match": ["no"], "source": "transcript.in_last_exon"}], "suggested_classification": null}, "external": {"comment": ""}, "frequency": {"comment": ""}, "reference": {"comment": ""}, "prediction": {"comment": ""}, "classification": {"comment": ""}}	1	2018-08-08 08:55:54.880155+00	\N	\N	8	HBOCUTV	v01	2	17	\N
\.

COPY public.allelereport (id, evaluation, user_id, date_created, date_superceeded, previous_report_id, allele_id, analysis_id, alleleassessment_id) FROM stdin;
1	{"comment": "REPORT_COMMENT &~øæå 1<br>"}	1	2018-08-08 08:49:40.486821+00	\N	\N	1	1	1
2	{"comment": "REPORT_COMMENT &~øæå 2<br>"}	1	2018-08-08 08:49:40.488808+00	\N	\N	2	1	2
3	{"comment": "REPORT_COMMENT &~øæå 3<br>"}	1	2018-08-08 08:49:40.489743+00	\N	\N	3	1	3
4	{"comment": "REPORT_COMMENT &~øæå 4<br>"}	1	2018-08-08 08:49:40.490626+00	\N	\N	4	1	4
5	{"comment": "REPORT_COMMENT &~øæå 5<br>"}	1	2018-08-08 08:49:40.491623+00	\N	\N	5	1	5
6	{"comment": "REPORT_COMMENT &~øæå 1<br>"}	1	2018-08-08 08:55:54.886021+00	\N	\N	7	2	6
7	{"comment": "REPORT_COMMENT &~øæå 2<br>"}	1	2018-08-08 08:55:54.887052+00	\N	\N	8	2	7
\.

COPY public.analysisinterpretation (id, genepanel_name, genepanel_version, user_state, state, status, finalized, date_last_update, date_created, analysis_id, workflow_status, user_id) FROM stdin;
1	HBOC	v01	{"allele": {"1": {"sections": {}, "allele_id": 1, "showExcludedReferences": false}, "2": {"sections": {}, "allele_id": 2, "showExcludedReferences": false}, "3": {"sections": {}, "allele_id": 3, "showExcludedReferences": false}, "4": {"sections": {}, "allele_id": 4, "showExcludedReferences": false}, "5": {"sections": {}, "allele_id": 5, "showExcludedReferences": false}}}	{"allele": {"1": {"report": {"included": false}, "allele_id": 1, "allelereport": {"evaluation": {"comment": "REPORT_COMMENT &amp;amp;~øæå 1<br>"}}, "verification": null, "alleleassessment": {"evaluation": {"acmg": {"included": [], "suggested": [{"op": "$in", "code": "REQ_GP_AD", "match": ["AD"], "source": "genepanel.inheritance"}, {"op": "$in", "code": "REQ_GP_last_exon_not_important", "match": ["LENI"], "source": "genepanel.last_exon_important"}, {"op": "$in", "code": "REQ_GP_LOF_missense", "match": ["ANY"], "source": "genepanel.disease_mode"}, {"op": "$in", "code": "REQ_not_in_last_exon", "match": ["no"], "source": "transcript.in_last_exon"}, {"op": "$in", "code": "REQ_null_variant", "match": ["stop_gained"], "source": "transcript.consequences"}, {"op": "$in", "code": "REQ_no_freq", "match": ["null_freq"], "source": "frequencies.commonness"}, {"op": null, "code": "PVS1", "match": null, "source": null}, {"op": null, "code": "PPxPM2", "match": null, "source": null}], "suggested_classification": null}, "external": {"comment": ""}, "frequency": {"comment": ""}, "reference": {"comment": ""}, "prediction": {"comment": ""}, "classification": {"comment": ""}}, "attachment_ids": [], "classification": "1"}, "referenceassessments": []}, "2": {"report": {"included": false}, "allele_id": 2, "allelereport": {"evaluation": {"comment": "REPORT_COMMENT &amp;amp;~øæå 2<br>"}}, "verification": null, "alleleassessment": {"evaluation": {"acmg": {"included": [], "suggested": [{"op": "$in", "code": "REQ_GP_AD", "match": ["AD"], "source": "genepanel.inheritance"}, {"op": "$in", "code": "REQ_GP_last_exon_not_important", "match": ["LENI"], "source": "genepanel.last_exon_important"}, {"op": "$in", "code": "REQ_GP_LOF_missense", "match": ["ANY"], "source": "genepanel.disease_mode"}, {"op": "$in", "code": "REQ_not_in_last_exon", "match": ["no"], "source": "transcript.in_last_exon"}, {"op": "$in", "code": "REQ_no_freq", "match": ["null_freq"], "source": "frequencies.commonness"}, {"op": null, "code": "PPxPM2", "match": null, "source": null}], "suggested_classification": null}, "external": {"comment": ""}, "frequency": {"comment": ""}, "reference": {"comment": ""}, "prediction": {"comment": ""}, "classification": {"comment": ""}}, "attachment_ids": [], "classification": "2"}, "referenceassessments": []}, "3": {"report": {"included": true}, "allele_id": 3, "allelereport": {"evaluation": {"comment": "REPORT_COMMENT &amp;amp;~øæå 3<br>"}}, "verification": null, "alleleassessment": {"evaluation": {"acmg": {"included": [], "suggested": [{"op": "$in", "code": "REQ_GP_AD", "match": ["AD"], "source": "genepanel.inheritance"}, {"op": "$in", "code": "REQ_GP_last_exon_not_important", "match": ["LENI"], "source": "genepanel.last_exon_important"}, {"op": "$in", "code": "REQ_GP_LOF_missense", "match": ["ANY"], "source": "genepanel.disease_mode"}, {"op": "$in", "code": "REQ_not_in_last_exon", "match": ["no"], "source": "transcript.in_last_exon"}, {"op": "$in", "code": "REQ_null_variant", "match": ["stop_gained"], "source": "transcript.consequences"}, {"op": "$in", "code": "REQ_no_freq", "match": ["null_freq"], "source": "frequencies.commonness"}, {"op": null, "code": "PVS1", "match": null, "source": null}, {"op": null, "code": "PPxPM2", "match": null, "source": null}], "suggested_classification": null}, "external": {"comment": ""}, "frequency": {"comment": ""}, "reference": {"comment": ""}, "prediction": {"comment": ""}, "classification": {"comment": ""}}, "attachment_ids": [], "classification": "3"}, "referenceassessments": []}, "4": {"report": {"included": true}, "allele_id": 4, "allelereport": {"evaluation": {"comment": "REPORT_COMMENT &amp;amp;~øæå 4<br>"}}, "verification": null, "alleleassessment": {"evaluation": {"acmg": {"included": [], "suggested": [{"op": "$in", "code": "REQ_GP_AD", "match": ["AD"], "source": "genepanel.inheritance"}, {"op": "$in", "code": "REQ_GP_last_exon_not_important", "match": ["LENI"], "source": "genepanel.last_exon_important"}, {"op": "$in", "code": "REQ_GP_LOF_missense", "match": ["ANY"], "source": "genepanel.disease_mode"}, {"op": "$in", "code": "REQ_not_in_last_exon", "match": ["no"], "source": "transcript.in_last_exon"}, {"op": "$in", "code": "REQ_null_variant", "match": ["frameshift_variant"], "source": "transcript.consequences"}, {"op": "$in", "code": "REQ_no_freq", "match": ["null_freq"], "source": "frequencies.commonness"}, {"op": null, "code": "PVS1", "match": null, "source": null}, {"op": null, "code": "PPxPM2", "match": null, "source": null}], "suggested_classification": null}, "external": {"comment": ""}, "frequency": {"comment": ""}, "reference": {"comment": ""}, "prediction": {"comment": ""}, "classification": {"comment": ""}}, "attachment_ids": [], "classification": "4"}, "referenceassessments": []}, "5": {"report": {"included": true}, "allele_id": 5, "allelereport": {"evaluation": {"comment": "REPORT_COMMENT &amp;amp;~øæå 5<br>"}}, "verification": null, "alleleassessment": {"evaluation": {"acmg": {"included": [], "suggested": [{"op": "$in", "code": "REQ_GP_AD", "match": ["AD"], "source": "genepanel.inheritance"}, {"op": "$in", "code": "REQ_GP_last_exon_not_important", "match": ["LENI"], "source": "genepanel.last_exon_important"}, {"op": "$in", "code": "REQ_GP_LOF_missense", "match": ["ANY"], "source": "genepanel.disease_mode"}, {"op": "$in", "code": "REQ_not_in_last_exon", "match": ["no"], "source": "transcript.in_last_exon"}, {"op": "$in", "code": "REQ_null_variant", "match": ["frameshift_variant"], "source": "transcript.consequences"}, {"op": "$in", "code": "REQ_no_freq", "match": ["null_freq"], "source": "frequencies.commonness"}, {"op": null, "code": "PVS1", "match": null, "source": null}, {"op": null, "code": "PPxPM2", "match": null, "source": null}], "suggested_classification": null}, "external": {"comment": ""}, "frequency": {"comment": ""}, "reference": {"comment": ""}, "prediction": {"comment": ""}, "classification": {"comment": ""}}, "attachment_ids": [], "classification": "5"}, "referenceassessments": []}}, "manuallyAddedAlleles": []}	Done	t	2018-08-08 08:49:40.497349+00	2018-08-08 08:47:55.402045+00	1	Interpretation	1
2	HBOCUTV	v01	{"allele": {"1": {"sections": {}, "allele_id": 1, "showExcludedReferences": false}, "2": {"sections": {}, "allele_id": 2, "showExcludedReferences": false}, "3": {"sections": {}, "allele_id": 3, "showExcludedReferences": false}, "7": {"sections": {}, "allele_id": 7, "showExcludedReferences": false}, "8": {"sections": {}, "allele_id": 8, "showExcludedReferences": false}}}	{"allele": {"1": {"report": {"included": false}, "allele_id": 1, "allelereport": {"evaluation": {"comment": "REPORT_COMMENT &amp;amp;~øæå 1<br>"}, "copiedFromId": 1}, "verification": null, "alleleassessment": {"reuse": true, "allele_id": 1, "evaluation": {"acmg": {"suggested": [{"op": "$in", "code": "REQ_GP_last_exon_important", "match": ["LEI"], "source": "genepanel.last_exon_important"}, {"op": "$in", "code": "REQ_GP_LOF_missense", "match": ["ANY"], "source": "genepanel.disease_mode"}, {"op": "$in", "code": "REQ_not_in_last_exon", "match": ["no"], "source": "transcript.in_last_exon"}, {"op": "$in", "code": "REQ_null_variant", "match": ["stop_gained"], "source": "transcript.consequences"}, {"op": "$in", "code": "REQ_no_freq", "match": ["null_freq"], "source": "frequencies.commonness"}, {"op": null, "code": "PVS1", "match": null, "source": null}, {"op": null, "code": "PPxPM2", "match": null, "source": null}]}}, "reuseCheckedId": 1}, "referenceassessments": []}, "2": {"report": {"included": false}, "allele_id": 2, "allelereport": {"evaluation": {"comment": "REPORT_COMMENT &amp;amp;~øæå 2<br>"}, "copiedFromId": 2}, "verification": null, "alleleassessment": {"reuse": true, "allele_id": 2, "evaluation": {"acmg": {"suggested": [{"op": "$in", "code": "REQ_GP_last_exon_important", "match": ["LEI"], "source": "genepanel.last_exon_important"}, {"op": "$in", "code": "REQ_GP_LOF_missense", "match": ["ANY"], "source": "genepanel.disease_mode"}, {"op": "$in", "code": "REQ_not_in_last_exon", "match": ["no"], "source": "transcript.in_last_exon"}, {"op": "$in", "code": "REQ_no_freq", "match": ["null_freq"], "source": "frequencies.commonness"}, {"op": null, "code": "PPxPM2", "match": null, "source": null}]}}, "reuseCheckedId": 2}, "referenceassessments": []}, "3": {"report": {"included": true}, "allele_id": 3, "allelereport": {"evaluation": {"comment": "REPORT_COMMENT &amp;amp;~øæå 3<br>"}, "copiedFromId": 3}, "verification": null, "alleleassessment": {"reuse": true, "allele_id": 3, "evaluation": {"acmg": {"suggested": [{"op": "$in", "code": "REQ_GP_last_exon_important", "match": ["LEI"], "source": "genepanel.last_exon_important"}, {"op": "$in", "code": "REQ_GP_LOF_missense", "match": ["ANY"], "source": "genepanel.disease_mode"}, {"op": "$in", "code": "REQ_not_in_last_exon", "match": ["no"], "source": "transcript.in_last_exon"}, {"op": "$in", "code": "REQ_null_variant", "match": ["stop_gained"], "source": "transcript.consequences"}, {"op": "$in", "code": "REQ_no_freq", "match": ["null_freq"], "source": "frequencies.commonness"}, {"op": null, "code": "PVS1", "match": null, "source": null}, {"op": null, "code": "PPxPM2", "match": null, "source": null}]}}, "reuseCheckedId": 3}, "referenceassessments": []}, "7": {"report": {"included": false}, "allele_id": 7, "allelereport": {"evaluation": {"comment": "<span style=\\"font-size: 14px; letter-spacing: normal; background-color: rgba(49, 129, 123, 0.05);\\">REPORT_COMMENT &amp;amp;~øæå 1</span><br>"}}, "verification": null, "alleleassessment": {"evaluation": {"acmg": {"included": [], "suggested": [{"op": "$in", "code": "REQ_GP_last_exon_important", "match": ["LEI"], "source": "genepanel.last_exon_important"}, {"op": "$in", "code": "REQ_GP_LOF_missense", "match": ["ANY"], "source": "genepanel.disease_mode"}, {"op": "$in", "code": "REQ_not_in_last_exon", "match": ["no"], "source": "transcript.in_last_exon"}, {"op": "$in", "code": "REQ_null_variant", "match": ["stop_gained"], "source": "transcript.consequences"}, {"op": "$in", "code": "REQ_no_freq", "match": ["null_freq"], "source": "frequencies.commonness"}, {"op": null, "code": "PVS1", "match": null, "source": null}, {"op": null, "code": "PPxPM2", "match": null, "source": null}], "suggested_classification": null}, "external": {"comment": ""}, "frequency": {"comment": ""}, "reference": {"comment": ""}, "prediction": {"comment": ""}, "classification": {"comment": ""}}, "attachment_ids": [], "classification": "1"}, "referenceassessments": []}, "8": {"report": {"included": false}, "allele_id": 8, "allelereport": {"evaluation": {"comment": "<span style=\\"font-size: 14px; letter-spacing: normal; background-color: rgba(49, 129, 123, 0.05);\\">REPORT_COMMENT &amp;amp;~øæå 2</span><br>"}}, "verification": null, "alleleassessment": {"evaluation": {"acmg": {"included": [], "suggested": [{"op": "$in", "code": "REQ_GP_last_exon_important", "match": ["LEI"], "source": "genepanel.last_exon_important"}, {"op": "$in", "code": "REQ_GP_LOF_missense", "match": ["ANY"], "source": "genepanel.disease_mode"}, {"op": "$in", "code": "REQ_no_aa_change", "match": ["synonymous_variant"], "source": "transcript.consequences"}, {"op": "$in", "code": "REQ_not_in_last_exon", "match": ["no"], "source": "transcript.in_last_exon"}], "suggested_classification": null}, "external": {"comment": ""}, "frequency": {"comment": ""}, "reference": {"comment": ""}, "prediction": {"comment": ""}, "classification": {"comment": ""}}, "attachment_ids": [], "classification": "2"}, "referenceassessments": []}}, "manuallyAddedAlleles": []}	Done	t	2018-08-08 08:55:54.890161+00	2018-08-08 08:47:55.557648+00	2	Interpretation	1
\.

COPY public.analysisinterpretationsnapshot (id, date_created, filtered, analysisinterpretation_id, allele_id, allelereport_id, presented_alleleassessment_id, alleleassessment_id, customannotation_id, presented_allelereport_id, annotation_id) FROM stdin;
1	2018-08-08 08:49:40.509939+00	\N	1	1	1	\N	1	1	\N	9
2	2018-08-08 08:49:40.513243+00	\N	1	2	2	\N	2	\N	\N	10
3	2018-08-08 08:49:40.514397+00	\N	1	3	3	\N	3	\N	\N	11
4	2018-08-08 08:49:40.515129+00	\N	1	4	4	\N	4	\N	\N	4
5	2018-08-08 08:49:40.515851+00	\N	1	5	5	\N	5	\N	\N	5
6	2018-08-08 08:49:40.516621+00	FREQUENCY	1	6	\N	\N	\N	\N	\N	\N
7	2018-08-08 08:55:54.894089+00	\N	2	8	7	\N	7	\N	\N	17
8	2018-08-08 08:55:54.895153+00	\N	2	1	1	1	1	1	1	9
9	2018-08-08 08:55:54.896033+00	\N	2	2	2	2	2	\N	2	10
10	2018-08-08 08:55:54.897325+00	\N	2	3	3	3	3	\N	3	11
11	2018-08-08 08:55:54.898293+00	\N	2	7	6	\N	6	\N	\N	12
\.

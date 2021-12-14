COPY public.customannotation (id, annotations, allele_id, user_id, previous_annotation_id, date_superceeded, date_created) FROM stdin;
2	{"prediction": {"ortholog_conservation": "conserved"}}	641	5	\N	2019-08-15 11:54:37.931995+00	2019-08-15 11:54:37.827861+00
3	{"prediction": {"ortholog_conservation": "conserved"}}	641	5	2	\N	2019-08-15 11:54:37.935855+00
\.

SELECT setval('customannotation_id_seq', (SELECT max(id) FROM customannotation));

COPY public.attachment (id, sha256, filename, size, date_created, mimetype, extension, user_id) FROM stdin;
1	317ae4ed2ccd78a142b094be6f558b2613b4f80c3d713579d4a89e9fed7d4e4b	image.png	57964	2019-08-15 11:50:19.082244+00	image/png	png	5
2	f7583cc9193fcbb631900cbf53d06c4af53543c904a2b94b54b4265efc70949d	image.png	71955	2019-08-15 11:55:54.635728+00	image/png	png	5
\.

SELECT setval('attachment_id_seq', (SELECT max(id) FROM attachment));

COPY public.alleleassessment (id, usergroup_id, classification, evaluation, user_id, date_created, date_superceeded, previous_assessment_id, allele_id, genepanel_name, genepanel_version, analysis_id, annotation_id, custom_annotation_id) FROM stdin;
1	2	2	{"acmg": {"included": [{"op": null, "code": "BS1", "uuid": "c6c05131-a95a-4591-94a9-7e8c5084acf8", "match": null, "source": "user", "comment": "<br>"}], "suggested": [{"op": "$in", "code": "REQ_GP_last_exon_important", "match": ["LEI"], "source": "genepanel.last_exon_important"}, {"op": "$in", "code": "REQ_GP_LOF_missense", "match": ["ANY"], "source": "genepanel.disease_mode"}, {"op": "$in", "code": "REQ_missense", "match": ["missense_variant"], "source": "transcript.consequences"}, {"op": "$in", "code": "REQ_not_in_last_exon", "match": ["no"], "source": "transcript.in_last_exon"}], "suggested_classification": 3}, "external": {"comment": "<br>"}, "frequency": {"comment": "<br>"}, "reference": {"comment": "<br>"}, "prediction": {"comment": "<br>"}, "classification": {"comment": "<br>"}}	5	2019-08-15 11:20:04.765692+00	\N	\N	1959	Mendeliome	v12	\N	1959	\N
2	2	5	{"acmg": {"included": [{"op": null, "code": "PVSxPM3", "uuid": "266ba7af-58b0-46f2-a869-215621133347", "match": null, "source": "user", "comment": "Seen in a significant amount of patients, both as homozygote, and as combined heterozygous with class 5 variants <font color=\\"#ff0000\\">(Supporting-0.5; Moderate-1; Strong 2-3; Very strong 4)</font><div><ul><li>The other variant is classified as 4 or 5: <font color=\\"#ff0000\\">trans-1 / phase unkown</font></li><li>Homozygote variant: <font color=\\"#ff0000\\">0.5</font></li><li>The other variant is classified as VUS: <font color=\\"#ff0000\\">trans-0.25</font></li><li>Homozygote variant in proband with related parents: <font color=\\"#ff0000\\">0.25</font></li></ul></div>"}, {"op": null, "code": "PMxPS3", "uuid": "5cce87bf-c02f-41e5-9788-c3fa662bb07a", "match": null, "source": "user", "comment": "In vivo functional study shows this variant to damage gene product (Rossetti S et al. (2003) Kidney Int.: 64(2), 391-403.)"}, {"op": null, "code": "PP3", "uuid": "7ea896a4-be41-498b-8c08-1e60222cccf0", "match": null, "source": "user", "comment": "Conserved"}, {"op": null, "code": "PP2", "uuid": "8e150340-3042-437e-9d52-033b1493715a", "match": null, "source": "user", "comment": "Very low rate of benign missense variation in PKHD1 (Gunay-Aygun M et al. (2010) Clin J Am Soc Nephrol: 5(6), 972-84.)"}], "suggested": [{"op": "$in", "code": "REQ_GP_AR", "match": ["AR"], "source": "genepanel.inheritance"}, {"op": "$in", "code": "REQ_GP_last_exon_important", "match": ["LEI"], "source": "genepanel.last_exon_important"}, {"op": "$in", "code": "REQ_GP_LOF_missense", "match": ["ANY"], "source": "genepanel.disease_mode"}, {"op": "$in", "code": "REQ_>=4affected", "match": ["in_many_aff"], "source": "refassessment.641_155.ref_population_affecteds"}, {"op": "$in", "code": "REQ_>=4affected", "match": ["in_many_aff"], "source": "refassessment.641_68.ref_population_affecteds"}, {"op": "$in", "code": "REQ_abnormal_protein", "match": ["prot_abnormal"], "source": "refassessment.641_68.ref_prot"}, {"op": "$in", "code": "REQ_in_trans_pathogenic", "match": ["in_trans_pathogenic"], "source": "refassessment.641_75.ref_phase"}, {"op": "$in", "code": "REQ_missense", "match": ["missense_variant"], "source": "transcript.consequences"}, {"op": "$in", "code": "REQ_not_in_last_exon", "match": ["no"], "source": "transcript.in_last_exon"}, {"op": "$in", "code": "REQ_protein_MQ", "match": ["prot_MQ"], "source": "refassessment.641_68.ref_prot_quality"}, {"op": "$all", "code": "PM3", "match": ["REQ_in_trans_pathogenic", "REQ_GP_AR"], "source": null}, {"op": "$all", "code": "PMxPS3", "match": ["REQ_abnormal_protein", "REQ_protein_MQ"], "source": null}, {"op": "$in", "code": "PP3", "match": ["conserved"], "source": "prediction.ortholog_conservation"}], "suggested_classification": 5}, "external": {"comment": "Reported 10+ times in ClinVar as pathogenic for ARPKD.<br><div><br></div><div><b>Integrated genetic/Laboratory Corporation of America:</b></div><div><i>Variant summary: The <span style=\\"background-color: rgb(102, 255, 51);\\">PKHD1 c.107C&gt;T (p.Thr36Met) </span>variant \\ninvolves the alteration of a conserved nucleotide.<span style=\\"background-color: rgb(253, 255, 22);\\"> 4/4 in silico tools \\npredict a damaging outcome for this variant.</span> This variant was found in \\n78/128548 control chromosomes at a frequency of 0.0006068, which does \\nnot exceed the estimated maximal expected allele frequency of a \\npathogenic PKHD1 variant (0.0070711). This variant has been reported in \\nmany ARPKD patients both as compound heterozygotes and homozygotes. In \\naddition, multiple clinical diagnostic laboratories/reputable databases \\nclassified this variant as pathogenic. One study of European cohorts \\ndetected more variant carriers in controls than in CRC patients, \\nindicating a possibly protective role of variant against CRC \\n(Ward_2011). Taken together, this variant is classified as pathogenic \\nfor ARPKD.&nbsp;</i><a href=\\"https://www.ncbi.nlm.nih.gov/clinvar/variation/4108/\\"></a><br></div><div><i><br></i></div><div><b>Invitae:</b></div><div><i>This sequence change replaces threonine with methionine at codon \\n36 of the PKHD1 protein (p.Thr36Met). The threonine residue is \\nmoderately conserved and there is a moderate physicochemical difference \\nbetween threonine and methionine. This variant is present in population \\ndatabases (rs137852944, ExAC 0.09%). This variant has been reported \\nextensively in individuals affected with autosomal recessive polycystic \\nkidney disease (ARPKD) (PMID: 11919560, 16199545, 12846734, 11898128, \\n15108281, 12506140). <span style=\\"background-color: rgb(253, 255, 22);\\">It is estimated that approximately 13% of ARPKD \\npatients of European origin have this variant</span>, making it the most common\\n mutation in that population (PMID: 21274727). Â¬â€&nbsp;ClinVar contains an \\nentry for this variant (Variation ID: 4108) For these reasons, this \\nvariant has been classified as Pathogenic.<br></i></div><div><i><br></i></div><div><b>GeneDX:</b></div><div><i>The T36M variant in the PKHD1 gene has been reported previously in\\n multiple individuals with autosomal recessive polycystic kidney disease\\n from a variety of ethnic backgrounds, indicating that in addition to a \\nfounder effect component, T36M may represent a mutational hotspot in the\\n PKHD1 gene (Ward et al., 2002; Bergmann et al., 2003; Bergmann et al., \\n2005; Melchionda et al., 2016). The T36M variant is observed in 57/66702\\n (0.085%) alleles from individuals of non-Finnish European background in\\n the ExAC dataset, and no individuals were reported to be homozygous \\n(Lek et al., 2016). T<span style=\\"background-color: rgb(253, 255, 22);\\">he T36M variant is a non-conservative amino acid \\nsubstitution, which is likely to impact secondary protein structure as \\nthese residues differ in polarity, charge, size and/or other properties.</span>\\n This substitution occurs at a position that is conserved across \\nspecies. In silico analysis predicts this variant is probably damaging \\nto the protein structure/function. We interpret T36M as a pathogenic \\nvariant.</i><br></div><div><i><br></i></div><div><b>Illumina:</b></div><div><i>Across a selection of the available literature, the <span style=\\"background-color: rgb(102, 255, 51);\\">PKHD1 \\nc.107C&gt;T</span> (p.Thr36Met) missense variant has been observed in a total \\nof 81 individuals with autosomal recessive polycystic kidney disease, \\nincluding in eight in a homozygous state (of whom two were siblings), in\\n 42 in a compound heterozygous state, and in 37 in a heterozygous state \\n(Ward et al. 2002; Bergmann et al. 2003; Furu et al. 2003; Sharp et al. \\n2005; Gunay-Aygun et al. 2010; Liu et al. 2014; Obeidova et al. 2015). \\n<span style=\\"background-color: rgb(253, 255, 22);\\">Haplotype analysis studies indicate that the p.Thr36Met variant occurs \\nin a mutational hotspot </span>(Bergmann et al. 2004), and suggest that the \\nvariant may have a single European origin (Consugar et al. 2005). This \\nvariant was absent from 510 controls but is reported at a frequency of \\n0.000932 in the European (non-Finnish) population of the Genome \\nAggregation Database. Based on the collective evidence, the p.Thr36Met \\nvariant is classified as pathogenic for autosomal recessive polycystic \\nkidney disease. This variant was observed by ICSL as part of a \\npredisposition screen in an ostensibly healthy population.</i><b><br></b></div>"}, "frequency": {"comment": "Reasonably uncommon in population databases (&lt;0.1%). Not seen as homozygous, possibly excluding them as unhealthy individuals.<br>"}, "reference": {"comment": "<br>"}, "prediction": {"comment": "Well conserved among 50+ species (Losekoot M et al. (2005) Hum. Genet.: 118(2), 185-206.)<div><br></div><h1>Ortholog conservation:</h1><div><img id=\\"4339a457-fcbf-45fc-98d3-fb49f98d7cc8\\" src=\\"/api/v1/attachments/2\\" alt=\\"Attachment 2 4339a457-fcbf-45fc-98d3-fb49f98d7cc8\\" title=\\"Attachment 2 4339a457-fcbf-45fc-98d3-fb49f98d7cc8\\" width=\\"662\\"><br></div>"}, "classification": {"comment": "<div>Missense variant in PKHD1 associated with ARPKD (Losekoot M et al. (2005) Hum. Genet.: 118(2), 185-206.). Common in patients with ARPKD (Ward CJ et al. (2002) Nat. Genet.: 30(3), 259-69.).</div>"}}	5	2019-08-15 12:00:50.907604+00	\N	\N	641	Ciliopati	v05	\N	641	3
\.

SELECT setval('alleleassessment_id_seq', (SELECT max(id) FROM alleleassessment));

COPY public.referenceassessment (id, reference_id, evaluation, user_id, date_created, date_superceeded, genepanel_name, genepanel_version, allele_id, previous_assessment_id, analysis_id) FROM stdin;
1	155	{"comment": "Seen in many patients", "sources": ["population_affecteds"], "relevance": "Yes", "ref_population_affecteds": "in_many_aff"}	5	2019-08-15 12:00:50.912847+00	\N	Ciliopati	v05	641	\N	\N
2	68	{"comment": "<span style=\\"background-color: rgb(253, 255, 22);\\">The most common mutation, c.107C&gt;T(T36M), has been described in each PKHD1 mutation study reported to date [9, 10, 21, 31, 33–35] and accounts for approximately 15% to 20% of mutated alleles. </span>There is conflicting data on whether it is an ancestral change oroccurs due to a frequent mutational event. Ultimately, it cannot be excluded that some of the mutated c.107C&gt;T alleles represent a founder effect in the Central European population where it is particularly frequent. However,<span style=\\"background-color: rgb(217, 3, 9);\\"> there is compelling evidence that T36M constitutes a mutational “hotspot,”</span> most likely due to methylation-induced deamination of the mutagenic CpG dinucleotide[36]. Within the present study, T36M was identified in a multitude of obviously unrelated families of different ethnic origins on various haplotypes. For instance, patients of nonconsanguineous Finnish family F2 homozygous for c.107C&gt;T were shown to harbor differing haplotypes. Further evidence of recurrence and against a common ancestral origin of mutated c.107C&gt;T alleles were demonstrated by diverse haplotypes among German-Austrian pedigrees F371 and ID206 carrying the same set of missense mutations (c.107C&gt;T+c.7264T&gt;G).<br>", "sources": ["population_affecteds", "protein"], "ref_prot": "prot_abnormal", "relevance": "Yes", "ref_prot_quality": "prot_MQ", "ref_auth_classification": "pathogenic", "ref_population_affecteds": "in_many_aff"}	5	2019-08-15 12:00:50.914644+00	\N	Ciliopati	v05	641	\N	\N
3	75	{"comment": "<img id=\\"eb76da83-195d-4ae6-a095-37d58633b0bd\\" src=\\"/api/v1/attachments/1\\" alt=\\"Attachment 1 eb76da83-195d-4ae6-a095-37d58633b0bd\\" title=\\"Attachment 1 eb76da83-195d-4ae6-a095-37d58633b0bd\\"><br>", "sources": ["segregation"], "ref_phase": "in_trans_pathogenic", "relevance": "Yes", "ref_quality": "excellent", "ref_auth_classification": "pathogenic"}	5	2019-08-15 12:00:50.915872+00	\N	Ciliopati	v05	641	\N	\N
\.

SELECT setval('referenceassessment_id_seq', (SELECT max(id) FROM referenceassessment));

COPY public.alleleassessmentreferenceassessment (alleleassessment_id, referenceassessment_id) FROM stdin;
2	1
2	2
2	3
\.

COPY public.allelereport (id, evaluation, user_id, date_created, date_superceeded, previous_report_id, allele_id, analysis_id, alleleassessment_id) FROM stdin;
1	{"comment": "<br>"}	5	2019-08-15 11:20:04.777913+00	\N	\N	1959	\N	1
2	{"comment": "<div><span style=\\"background-color: transparent;\\">Disease causing variant in PKHD1 associated with autosomal recessive kidney disease 4 (APRKD, OMIM #263200), which is a cilie-related disease characterized by affected kidneys and congenital hepatic fibrosis. PKHD1 is a coding gene for the protein fibrocystin, located in the cell membrane in kidney cells, and is assumed to be involved in tubulogenesis and/or sustaining correct orientation of the epithelial cells in kidney tubuli.</span><br></div><div><br></div><div>The variant c.107C&gt;T (p.Thr36Met) in PKHD1 has been reported in homozygote and combined heterozygote form i many patients with ARPKD, and is therefore a certain disease causing variant.</div>"}	5	2019-08-15 12:00:50.925468+00	\N	\N	641	\N	2
\.

SELECT setval('allelereport_id_seq', (SELECT max(id) FROM allelereport));

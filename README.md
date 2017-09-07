# dicom-ontology
This repository contains the DICOM ontology used by the INCF-NIDASH NIDM-Experiment project.

The terms originated from the DICOM XML docbook that contains all of the DICOM tag information.
This file originated from David Clunie.

In addition, defined based terms were extracted from the DICOM documentation and organized into a heirarchy.

The term ID is written as:
1) dicom_0000XXXX in which X stands for a number. These terms are extracted from the DICOM documentation.
2) dicom_xxxxxxxx in which the DICOM tag is represented by 'xxxxxxxx'.

In this ontology, the "mu"'s that were originally used for "micro" were replaced by "u"'s to make the text handling
easier. The labels used here are those extracted from the DICOM docbook.

Tags that were incorporated into Neurolex in earlier work have a owl:sameAs nlx_xxxxxx statement where "xxxxxx" 
is the original Neurolex ID number.

# dicom-ontology
This repository contains the DICOM ontology used by the INCF-NIDASH NIDM-Experiment project.

The terms came from the DICOM XML docbook that contains all of the DICOM information.
This file originated from David Clunie.

There are a number of non-alphanumeric characters in the dicom tag labels, things like "/", "_", "-" and the Greek letter mu 
used as an abbreviation for "micro".  In this ontology, the "mu"'s were replaced by "u"'s to make the text handling
easier. All non-alphanumberic characters and spaces were removed from the labels and camel case implmented
to make the actual term (e.g. "Field of View Dimension(s) in Float" becomes "fieldOfViewDimensionsInFloat")

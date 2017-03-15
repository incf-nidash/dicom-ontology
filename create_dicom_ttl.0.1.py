'''
  This code takes the DICOM terms from the DICOM XML docbook 
  (provided by David Clunie) and creates a basic turtle file 
  - just the class entries.  No header and no properties. 

  Issues to be resolved: 
  1) I'd like to have an entry for the tag ID in the correct format (XXXX,XXXX)
     as well as the VR and category (hardware, patient,etc). I will have 
     to either find or define terms for these.  Should 
     they be defined in the dicom: namespace or somewhere else?

  2) Which properties? Use those from Neurolex? Define those needed?

  3) What's happening to the terms defined in Neurolex? Are they included
     in SciCrunch?  Do they retain the Neurolex ID or get a new one?

ver 0.1 2017-03-10
Karl Helmer
Athinoula A. Martinos Center for Biomedical Imaging
Massachusetts General Hospital

'''

import os, sys
import re

#************************************************
#input parameters
#outDir = '/home/karl/Work/INCF/nidm/nidm/nidm/nidm-experiment/imports/'
outDir = '/home/karl/Work/INCF/terms/code/'
outFile = 'dicom.ttl'
# the following file version is the one that replaces the greek mu with "u"
# the former means I have to deal with unicode processing 
inFile = '/home/karl/Work/INCF/terms/code/Clunie_DICOM_definitions-us.txt'
dicomNS = 'dicom:'
rdfType = 'rdf:type'
owlClass = 'owl:Class'
rdfsLabel = 'rdfs:label'
rdfsSub = 'rdfs:subClassOf:'
dicomTag = 'nidm:dicomTag'
dcID = 'dc:identifier'
labelStr = 'label'
subClass = 'subClassOf'
provNS = 'prov:'
xsdString = '^^xsd:string ;'
definitionStr = 'obo:IAO_0000115'
editorNote = 'obo:IAO_0000116 "To be discussed."^^xsd:string ;'
curationStatusReady = 'obo:IAO_0000114  obo:IAO_0000122 ;'
curationStatusReqDisc = 'obo:IAO_0000114  obo:IAO_0000428 ;'
classLink = '###  http://purl.org/nidash/dicom#'
#************************************************

def write_ontology_header(ttlFile):

    ttlFile.write("@prefix : <http://www.semanticweb.org/owl/owlapi/turtle#> .\n")
    ttlFile.write("@prefix owl: <http://www.w3.org/2002/07/owl#> .\n")
    ttlFile.write("@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .\n")
    ttlFile.write("@prefix xml: <http://www.w3.org/XML/1998/namespace> .\n")
    ttlFile.write("@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n")
    ttlFile.write("@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n")
    ttlFile.write("@prefix nidm: <http://www.incf.org/ns/nidash/nidm#> .\n")
    ttlFile.write("@prefix dc: <http://purl.org/dc/terms/> .\n")
    ttlFile.write("@base <http://www.owl-ontologies.com/Ontology1298855822.owl> .\n")
    ttlFile.write("\n")
    ttlFile.write("<http://purl.org/nidash/nidm/dicom#> rdf:type owl:Ontology .\n")


def write_class_header(ttlFile):
    ttlFile.write('\n')
    ttlFile.write('#################################################################\n')
    ttlFile.write('#\n')
    ttlFile.write('#    Classes\n')
    ttlFile.write('#\n')
    ttlFile.write('#################################################################\n')
    ttlFile.write('\n')
    


def repl_func(m):
    """process regular expression match groups for word upper-casing problem"""
    return m.group(1) + m.group(2).upper()


def create_camelcase_label(s):
    '''Capitalizes each word, removes non-alphanumeric characters 
       and spaces from the label  '''
    s = re.sub("(^|\s)(\S)", repl_func, s)
    s = re.sub('[^a-zA-Z0-9]+',"", s)
    s.replace(" ", "")
    if s[0].isalpha:
        s = s[0].lower() + s[1:]

    return s


def main():
    newInfo = []
    ttlFile = open(outDir+outFile, "w")

    write_ontology_header(ttlFile)
    write_class_header(ttlFile)

    # get the label, tag, definition for each term
    dicomInfo = open(inFile, "r")
    lines = dicomInfo.readlines()
    for line in lines:
        #print line
        labelGroup = re.search(r'.*Name="([A-Za-z0-9\s\-\/\(\)\'\&]*)"\t', line)
        label = labelGroup.group(1)
        #print label
        tagGroup = re.search(r'.*Tag=("[A-Za-z0-9\s\,\(\)]*")\t', line)
        tag = tagGroup.group(1)  #left the quotes around the tag
        #print tag
        definitionGroup = re.search(r'.*Description=(".*)', line)
        definition1 = definitionGroup.group(1)
        definition = definition1  # has quotes already
        #print definition

        labelCC = create_camelcase_label(label)
        #print label
        ttlFile.write('###  http://purl.org/nidash/dicom#'+labelCC+"\n")
        ttlFile.write("\n")
        ttlFile.write(dicomNS+labelCC+" "+rdfType+" "+owlClass+"  ;\n")
        ttlFile.write("\n")
        ttlFile.write("        "+rdfsLabel+" "+'"'+label+'"'+xsdString+"\n")
        ttlFile.write("\n")
        ttlFile.write("        "+curationStatusReqDisc+"\n")
        ttlFile.write("\n")
        ttlFile.write("        "+definitionStr+" "+definition+xsdString+"\n")
        ttlFile.write("\n")
        ttlFile.write("        "+dicomTag+" "+tag+xsdString+"\n")
        ttlFile.write("\n")
        ttlFile.write("        "+rdfsSub+" "+dcID+"  .\n")
        ttlFile.write("\n")
        ttlFile.write("\n")
        ttlFile.write("\n")

    ttlFile.close()


##############################################################
if __name__ == "__main__":
    main()

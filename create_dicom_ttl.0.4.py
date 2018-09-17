'''
  This code takes the DICOM terms from the DICOM XML docbook 
  (provided by David Clunie) and the CSV file from the DICOM terms
  from Neurolex and creates a basic turtle file. Note that in the 
  definitions there are XML links that don't show up in the extracted
  text file from the DICOM docbook.  There are then phrases like
  "See " that need to be removed from the definitions at the very end.

ver 0.1 2017-03-14 - original; terms are camelcase labels
ver 0.2 2017-03-28 - retrieve Neurolex ID's using term labels
ver 0.3 2017-03-29 - retrieve neurolex ID using DICOM tags
ver 0.4 2017-04-19 - change ID system to non-tag-based ID's
                     reserve first 500 for other terms, rest for tags

Karl Helmer
Athinoula A. Martinos Center for Biomedical Imaging
Massachusetts General Hospital

'''

import os, sys
import re
from operator import itemgetter
import pickle

#************************************************
#input parameters
#outDir = '/home/karl/Work/INCF/nidm/nidm/nidm/nidm-experiment/imports/'
outDir = '/home/karl/Work/INCF/dicom-ontology/'
outFile = 'dicom_numericalID.ttl'
tagDefFile = 'all_tag_definition.txt'
# The following file version is the one that replaces the greek mu with "u"
# Use of mu means dealing with unicode processing 
inFile = '/home/karl/Work/INCF/dicom-ontology/Clunie_DICOM_definitions-us.txt'
nlxFile = '/home/karl/Work/INCF/dicom-ontology/Neurolex_dicom_terms_result.csv'
dicomNS = 'dicom:'
dicomPrefix = 'dicom_'
rdfType = 'rdf:type'
owlClass = 'owl:Class'
owlDatatypeProperty = 'owl:DatatypeProperty'
owlSameAs = 'owl:sameAs'
rdfsLabel = 'rdfs:label'
rdfsSub = 'rdfs:subClassOf'
dicomTag = dicomNS+'dicom_00000065'#'Tag'
vrInDicom = dicomNS+'VR'
nlxID = 'nidm:neurolexID'
dcID = 'dc:identifier'
labelStr = 'label'
subClass = 'subClassOf'
provNS = 'prov:'
xsdString = '^^xsd:string '
definitionStr = 'obo:IAO_0000115'
editorNote = 'obo:IAO_0000116 "To be discussed."'
curationStatusReady = 'obo:IAO_0000114  obo:IAO_0000122 '
curationStatusReqDisc = 'obo:IAO_0000114  obo:IAO_0000428 '
classLink = 'http://purl.org/nidash/dicom#'
nlxLink = 'http://uri.neuinfo.org/nif/nifstd/'
idStart = 500
#************************************************

def write_ontology_header(ttlFile):

    ttlFile.write("@prefix : <http://www.semanticweb.org/owl/owlapi/turtle#> .\n")
    ttlFile.write("@prefix owl: <http://www.w3.org/2002/07/owl#> .\n")
    ttlFile.write("@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .\n")
    ttlFile.write("@prefix xml: <http://www.w3.org/XML/1998/namespace> .\n")
    ttlFile.write("@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n")
    ttlFile.write("@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n")
    ttlFile.write("@prefix nidm: <http://www.incf.org/ns/nidash/nidm#> .\n")
    ttlFile.write("@prefix dc: <http://purl.org/dc/elements/1.1/> . .\n")
    ttlFile.write("@prefix obo: <http://purl.obolibrary.org/obo/> .\n")
    ttlFile.write("@prefix nlx: <http://uri.neuinfo.org/nif/nifstd/> .\n")
    ttlFile.write("@base <http://www.owl-ontologies.com/Ontology1298855822.owl> .\n")
    ttlFile.write("\n")
    ttlFile.write(classLink+"[ rdf:type owl:Ontology ] .\n")


def write_class_header(ttlFile):
    ttlFile.write('\n')
    ttlFile.write('#################################################################\n')
    ttlFile.write('#\n')
    ttlFile.write('#    Datatype Properties\n')
    ttlFile.write('#\n')
    ttlFile.write('#################################################################\n')
    ttlFile.write('\n')
    

# The following two functions are used to create camelCase version of DICOM tag label
#def repl_func(m):
#    """process regular expression match groups for word upper-casing problem"""
#    return m.group(1) + m.group(2).upper()


#def create_camelcase_label(s):
#    '''Capitalizes each word, removes non-alphanumeric characters 
#       and spaces from the label  '''
#    s = re.sub("(^|\s)(\S)", repl_func, s)
#    s = re.sub('[^a-zA-Z0-9]+',"", s)
#    s.replace(" ", "")
#    if s[0].isalpha:
#        s = s[0].lower() + s[1:]
#
#    return s


# The following two functions are used to match term labels from the two input files
# Used in string_match function
def max_list_value(list,i):
    # this function returns a tuple of the (index, maxValue) for a list
    # you supply the list and the index of the place within the list that you 
    # want the max of.
    return max(enumerate(sub[i] for sub in list), key=itemgetter(1))


def string_match(label,nlxData):
    # this code takes an input string (dicom tag label) and tries to find an 
    # exact match in another list of labels. If no exact match is found, finds 
    # the closest match from a list of labels in which there is at least one 
    # match between the original label and the possible label.

    # find the length of the list of possible labels
    neuroLines = len(nlxData)
    exactMatch = 'False'
    noMatch = 'True' 

    print "considering DICOM file label = "+label

    for i in range(neuroLines):
        partMatch = 'False'
        tempStore = []
        # check for exact match
        #print "DICOM_label=",label, " nlxData_label=",nlxData[i][0]
        if nlxData[i][0] == label:
            vrCode = nlxData[i][3]
            dicomTagID = nlxData[i][2]
            neurolexID = nlxData[i][1]
            print "match for ", label
            exactMatch = 'True'
            noMatch = 'False'
            break
    # if no exact match, find how many words in the orig label are in the possible label 
    # if none, go to next nlxLabel in nlxData
        else:
            matchCount = 0
            labelPart = label.split()
            filteredLabelPart = [s for s in labelPart if len(s) > 2] #don't match 2-or-less length words
            for lp in filteredLabelPart:
                #print lp
                if lp in nlxData[i][0]:
                    matchCount = 1+matchCount

            # if at least one matching word, store needed info as list in list tempStore
            if matchCount != 0:
                partMatch = 'True'
                tempStore.append([nlxData[i][0], nlxData[i][2], nlxData[i][1], nlxData[i][3], matchCount])

    if (partMatch == 'True') and (exactMatch == 'False'):
        print "Dicom label = "+label+"\n"
        print "Neurolex entry = ", tempStore

        if len(tempStore) > 1: #if only a single term matches then assume that it's not a match
            isMatch = input("Is this a match (1/0)?")
            if isMatch:
                print 'partial match for '+label
                maxAndWhere = max_list_value(tempStore,-1)  # tuple
                print maxAndWhere
                k=maxAndWhere[0]    #put the index of the best match into k
                # put values for best match into variables for return 
                neurolexID = tempStore[k][2]
                dicomTagID = tempStore[k][1]
                vrCode = tempStore[k][3]
                noMatch = 'False'
            else:
                partMatch = 'False'
        else:
            partMatch = 'False'

    if (partMatch == 'False') and (exactMatch == 'False'):
        noMatch = 'True'
        neurolexID = 'NF'
        dicomTagID = 'NF'
        vrCode = 'NF'
        print "no match for "+label
            
    return neurolexID, dicomTagID, vrCode, noMatch



def tag_match(tag,nlxData):
    '''
    This code takes an input string (dicom tag) and tries to find an 
    exact match in another list of labels. The two strings have different
    initial formats so first have to put them in common format (8char string,
    no non-alphanumeric characters)
    '''

    # set match status flags
    neuroLines = len(nlxData)
    noMatch = 'True'
    neurolexID = 'NF'
    vrCode = 'NF'

    # get the DICOM tag from the Clunie file in the format (XXXX,XXXX)
    dicomTagIDGroup = re.search(r'.*\(([A-Za-z0-9\,]*)\)', tag)
    if not dicomTagIDGroup:
        print "bad dicom tag format for: "+tag
    else:
        dicomTagPartsList = dicomTagIDGroup.group(1).split(",")
        dicomTagID = dicomTagPartsList[0]+dicomTagPartsList[1]
        #print dicomTag

    for i in range(neuroLines):
        # This assumes that the correctly formatted tag is present 
        # (already checked in main)
        # To get the from XXXX_XXXX to XXXXXXXX
        nlxDicomTagPartsList = nlxData[i][2].split("_")
        nlxDicomTagID = nlxDicomTagPartsList[0]+nlxDicomTagPartsList[1]
        #print nlxDicomTag

        # check for exact match
        if nlxDicomTagID == dicomTagID:
            vrCode = nlxData[i][3]
            neurolexID = nlxData[i][1]
            noMatch = 'False'
            break
        else:
            pass


    if noMatch == 'True':
        print "no match for "+dicomTagID
    else:
        print "match for "+dicomTagID

    return neurolexID, dicomTagID, vrCode, noMatch



def main():
    nlxData = []
    neurolexID = ''
    dicomTagID = ''
    vrCode = ''
    ttlFile = open(outDir+outFile, "w")

    write_ontology_header(ttlFile)
    write_class_header(ttlFile)

    # Neurolex/Interlex section*****************************
    # put the label, Neurolex ID (if present), DICOM ID, and VR into a file that will be
    # matched up to the label from the DICOM (Clunie-supplied) file 
    nlxFileData = open(nlxFile, "r")
    entries = nlxFileData.readlines()
    for entry in entries:

        dicomIDGroup = re.search(r'.*DICOM:([A-Za-z0-9\_]*),', entry)
        if not dicomIDGroup:
            print "no dicom ID found in: ", entry
            dicomID = "NF "
        else:
            dicomID = dicomIDGroup.group(1)
            #print dicomID


        nlxIDGroup = re.search(r'.*,(nlx_[0-9]*),', entry)
        if not nlxIDGroup:
            print "no nlx ID found in: ", entry
            nlxID = "NF "
        else:
            nlxID = nlxIDGroup.group(1)
            #print nlxID 


        vr =  entry[-3:].rstrip("\n")  #get rid of newline character 
        vrGroup = re.search(r'(\"\,*)', vr)
        if vrGroup:
            if "US or SS" in entry:
                vr = "US or SS"
            elif "OB or OW" in entry:
                vr = "OB or OW"
            elif "OW or OB" in entry:
                vr = "OB or OW"
            elif "OP or OW" in entry:
                vr = "OP or OW"
            elif "US,SS,or OW" in entry:
                vr = "US or SS"
            elif "US or SS or OW" in entry:
                vr = "US or SS or OW"
            elif "does not exist" in entry:
                vr = "does not exist"
            else:
                print "bad or missing VR value found in: ", entry
                vr = "NF "
        else:
            vr = vr

        #vr = vr.rstrip("\n")  #get rid of the newline character that appears 

        # problem her is that sometimes there are "" around Category sometimes not
        dicomLabelGroup =  re.search(r'.*:Category:([A-Za-z0-9\s\-\/\(\)\'\&\"]*),', entry)
        if not dicomLabelGroup:
            print "no dicom label found in: ", entry
            dicomLabel = "NF "
        else:
            dicomLabel = dicomLabelGroup.group(1)
            if dicomLabel[-1] == '"':
                dicomLabel = dicomLabel[:-1]
            #print dicomLabel

        # store extracted strings in a list for future retrieval - this is all relevant NLX data
        nlxData.append([dicomLabel, nlxID, dicomID, vr])


    # DICOM document section************************************
    # get the label, tag, definition for each term
    tagList = []
    multiTags = []
    allEntries = []
    idStart = 500
    dicomFileData = open(inFile, "r")
    lines = dicomFileData.readlines()
    for line in lines:

        # create a 5 digit ID with leading zeros to ID the tags
        idStart = idStart + 1
        numericalTagID = str(idStart).zfill(5)
 
        # get the label
        labelGroup = re.search(r'.*Name="([A-Za-z0-9\s\-\/\(\)\'\&]*)"\t', line)
        label = labelGroup.group(1)
        # get the tab
        tagGroup = re.search(r'.*Tag=("[A-Za-z0-9\s\,\(\)]*")\t', line)
        tag = tagGroup.group(1)  #left the quotes around the tag
        # get the definition
        definitionGroup = re.search(r'.*Description=(".*)', line)
        definition = definitionGroup.group(1) # has quotes already

        # find the corresponding term from the extracted Neurolex info
        #neurolexID, dicomTagID, vrCode, noMatch = string_match(label,nlxData)
        neurolexID, dicomTagID, vrCode, noMatch = tag_match(tag,nlxData)

        #tempList = [dicomTagID, definition]
        #allEntries.append(tempList)

        # determine which tags have multiple entries and create a non-repeating list
        # of the multiple-entry tag (multitags). tagList is a non-repeating list of all tags.
        # {just store tag}
        #if dicomTagID in tagList and dicomTagID not in multiTags:
        #    multiTags.append(dicomTagID)
        #else:
        #    tagList.append(dicomTagID)

        #{store all multiple tags and their definitions} - HOW TO STORE FIRST ONE OF MULTIPLE?
        # look at each tag in turn and all tags after that tag.
        #if dicomTagID in tagList and dicomTagID not in multiTags:
        #    tempList = [dicomTagID, definition]
        #    multiTags.append(tempList)
        #else:
        #    tagList.append(dicomTagID)

        #labelCC = create_camelcase_label(label)
        #print label
        ttlFile.write("###  "+classLink+dicomPrefix+numericalTagID+"\n")
        ttlFile.write("\n")
        ttlFile.write(dicomNS+dicomPrefix+numericalTagID+" "+rdfType+" "+owlDatatypeProperty+"  ;\n")
        ttlFile.write("\n")
        ttlFile.write("        "+rdfsLabel+" "+'"'+label+'"'+xsdString+";\n")
        ttlFile.write("\n")
        ttlFile.write("        "+curationStatusReqDisc+";\n")
        ttlFile.write("\n")
        ttlFile.write("        "+definitionStr+" "+definition+xsdString+";\n")
        ttlFile.write("\n")
        ttlFile.write("        "+dicomTag+" "+tag+xsdString+";\n")
        ttlFile.write("\n")

        if noMatch == 'False':
            ttlFile.write("        "+owlSameAs+" "+nlxID+"  ;\n")
            ttlFile.write("\n")
            ttlFile.write("        "+vrInDicom+" "+'"'+vrCode+'"'+xsdString+"  ;\n")
            ttlFile.write("\n")
            ttlFile.write("        "+rdfsSub+" "+dcID+"  .\n")
        else:
            ttlFile.write("        "+rdfsSub+" "+dcID+"  .\n")

        ttlFile.write("\n")

        ttlFile.write("\n")
        ttlFile.write("\n")

    ttlFile.close()

    #print multiTags
    #print len(multiTags)

    # write out the list of all tag and defs for later sorting
    #with open(outDir+tagDefFile, "wb") as fp:
    #    pickle.dump(allEntries,fp)
    #fp.close()
##############################################################
if __name__ == "__main__":
    main()

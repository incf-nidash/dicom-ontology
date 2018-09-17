'''
  This code checks each entry in the dicom_ontology.owl file for an
  explicit VR assignment.  The issue is that the "new" entries - 
  the entries/tags not in the original set that were scraped from
  the NEMA website and instantiated in Neurolex - do not have
  VR values attached. The reason for this is that in the DICOM 
  standard documentation a listing of all of the tags are in Parts
  06 and 07, but these lists do not include the definitions. The
  definitions are given in tables in other Parts, so have to 
  be extracted from those tables.

  This code checks to see if an entry specifies the VR value and 
  if not, retrieves it from the file 
  /home/karl/Work/INCF/XML_code/dicom_dict_vr.py
  which was created by the code: 
  /home/karl/Work/INCF/XML_code/vr_generate_dict.py

  This code skips reads lines until it finds 
  a line containing "Datatype Properties" and continues to read lines 
  until is finds a line that contains "dicom#dicom".  It collects 
  lines in the variable "entry" until it encounters a line containing 
  " ." which is the ending character for an entry. If it finds
  a line containing "dicom:VR" then it writes the entry after removing 
  an extra blank line that was written into the original owl file as
  the line previous to the line containing the VR info. The code then 
  writes that entry to the output file and then reads on, collecting the 
  next entry. If the entry does not contain VR line, it queries the 
  dicom_dict_vr.py file to find the VR value and writes a line 
  containing the VR value in the correct format.

  Note that since the code starts collecting entries with the "Datatype
  Properties" section, everything above that needs to be pasted into 
  the resulting file to make a complete owl file.  Also, the Class section
  will be unchanged since there are no VR values for these terms
  (since they are not official DICOM tags, but terms I extracted from the 
  official Part documents). The code checks for the presence of "xxxx" in 
  the dicom tag. If that string is in the tag then just write the entry 
  unchanged into the output file.


Sample Complete Entry
------------------------------------------------
###  http://purl.org/nidash/dicom#dicom_00280011

dicom:dicom_00280011 rdf:type owl:DatatypeProperty ;

        rdfs:label "Columns"^^xsd:string ;

        obo:IAO_0000114  obo:IAO_0000428 ;

        obo:IAO_0000115 "Number of columns in the image."^^xsd:string ;

        dicom:dicom_xxxx0065 "(0028,0011)"^^xsd:string ;

        dicom:VR "US"^^xsd:string ;

        rdfs:subClassOf dc:identifier .


2018-09-04 - started
2018-09-14 - ran on full owl file and checked result into GitHub repo 

Karl Helmer
Athinoula A. Martinos Center for Biomedical Imaging
Massachusetts General Hospital, 2018

'''

import os, sys
import re
import ast

#************************************************
#input parameters
inDir = '/home/karl/Work/INCF/dicom-ontology/'
inFilename = 'dicom_ontology.owl'
outDir = '/home/karl/Work/INCF/dicom-ontology/'
outFilename = 'dicom_ontology_new.owl'
vrDir = '/home/karl/Work/INCF/XML_code/'
vrFilename = 'dicom_dict_vr.dict'
startEntry = 'dicom#dicom'
endEntry = ' .'
startPlace = 'Datatype Properties'
#************************************************

def search_vr(entry):
    #make 1 string rather than searching in each string individually
    #this is faster than using some version of "any"
    combined = ' '.join(entry) 
    test = 'dicom:VR' in combined

    return test


def get_tag(entry):

    # check each line in entry for the dicom tag
    for e in entry:
        if 'rdf:type' in e:
            t = re.search('dicom_(.+?) ', e)
            tag = t.group(1)
            if tag:
                #print "The DICOM tag is: ", tag
                return tag
            else:
                #this will crash the program since no tag value is returned
                print "no dicom tag value found in: ", entry 
    

def get_vr(vrDir, vrFilename, tag):
    if tag:
        vrF = open(vrDir+vrFilename, 'r').read()
        dicomDict = ast.literal_eval(vrF)
        if tag:
            vr = dicomDict.get(tag,'')[0]
            #print "vr value is = ", vr    
            return vr
    else:
        print "vr value not found for tag = ", tag
        return None


def add_vr_to_entry(vr, entry):
    vrLine = '        dicom:VR "{}"^^xsd:string   ;\n'.format(vr)
    entry.insert(4,vrLine)
    entry.insert(5,'\n')

    return entry


def write_entry(entry, outFile):
    for line in entry:
        outFile.write(line)
    outFile.write('\n\n')


def remove_sequential_blanks_in_entry(entry):
    for i in range(len(entry)-1):
        if entry[i] == entry[i+1]:
            del entry[i]
            break

    return entry



def main():

    # open the dicom ontology file and start reading
    with open(inDir+inFilename, 'r') as inFile, open(outDir+outFilename, 'w') as outFile:
        entry = []
        copy = False 
        dt = False
        for line in inFile: 
            if startPlace in line: #find "Datatype Properties" line and start here
                dt = True
                print "starting place is:", startPlace

            if dt == True: #start check after Datatype Prop line
                if startEntry in line:
                    copy = True
                    #print 'start of entry'
                if endEntry in line:
                    copy = False
                    entry.append(line)        #append the last line of entry
                    #print 'end of entry'

                    #now check the entry list as a whole
                    vrFlag = search_vr(entry) #see if the entry has a VR line
                    tag = get_tag(entry)  #extract the tag from entry
                    print tag, vrFlag
                    if vrFlag == False and ("xxxx" not in tag):
                        vr = get_vr(vrDir, vrFilename, tag)      #get vr value from the dict
                        entry1 = add_vr_to_entry(vr, entry)
                        write_entry(entry1, outFile)    #write entry with added vr to outfile
                        entry = []            #clear entry list when finished
                    else:
                        entry2 = remove_sequential_blanks_in_entry(entry)
                        write_entry(entry2, outFile)    #write unchanged entry to outfile
                        entry = []
                elif copy:
                    entry.append(line)



##############################################################
if __name__ == "__main__":
    main()

#!/usr/bin/python
# -*- coding: utf-8 -*-

# generate_dict_2015b.py

"""
    Reformat a dicom dictionary PS06 and etc docbook xml files (from e.g. standard docs) to Python syntax
    Write the main DICOM dictionary elements as a python dict called main_attributes with format:
    Tag: ('Attribute Name', 'Attribute Description')
    Where
        Tag is a string representation of the (group, element) as "ggggeeee" (e.g. 00181600)
        Attribute Name is the Tag label
        Attribute Description is the Tag defnition
"""

# Based on Rickard Holmberg's docbook_to_dict2013.py
# http://code.google.com/r/rickardholmberg-pydicom/
# but rewritten for not using bs4 (and slight change for standard v2015b)

# Based on Rickard Holmberg's generate_dict_2015b.py - found online as part of the "pydicom" package.
# Modified to get a table with the tags and VR values - vr_generate_dict.py
# This code extracts the definitions from Part 03, but note that the relevant tables don't
# also include the VR values. This code is used to generate a python 
# dict that contains tags and VR's. I keep the code to get latest docbook from URL, 
# but currently pull from offline/local version of latest docbook so I don't have to be online.
# This writes out the table rows as a single dictionary. 
# K. Helmer
# Massachusetts General Hospital, 2018

import urllib2
import xml.etree.ElementTree as ET
import os

pydict_filename = 'dicom_dict_def.dict'  # KGH 

def write_dict(f, attributes, tagIsString):  #KGH-write out the tag as a string in both cases
    if tagIsString:
        entry_format = """"{Tag}": ("{Attribute Name}", "{Attribute Description}")"""  #KGH - try double quotes because some Names have apostrophe's in them, e.g., "Referring Physician's Name"
    else:
        entry_format = """"{Tag}": ("{Attribute Name}", "{Attribute Description}")"""  #KGH - try double quotes because some Names have apostrophe's in them, e.g., "Referring Physician's Name"

    #f.write("\n%s = {\n    " % dict_name)
    #f.write("%s = {\n    " % dict_name)   #KGH - no initial newline necessary + don't want "name = {}"
    f.write("{\n    ")      #KGH - just start with dict "{"
    f.write(",\n    ".join(entry_format.format(**attr) for attr in attributes))
    f.write("\n}\n")



def parse_header(header_row):
    """ Parses the table's thead/tr row, header_row, for the column headers """
    field_names = []

    # The header_row should be <thead><tr>...</tr></thead>
    # Which leaves the following:
    # In the Part 06 and Part 07 sections docbook tables use:
    #   <th><para><emphasis>Header 1</emphasis></para></th>
    #   <th><para><emphasis>Header 2</emphasis></para></th>
    #   etc...
    # But in Part 03 the <emphasis> tag is not used.  This means that we have:
    #   <th><para>Header 1</para></th>
    #   <th><para>Header 2</para></th>
    #   inside the <thead></thead> block
    # so each para element inside <thead> is the column heading
    # (although it looks as though the table column headings are still bold
    # when displayed in the pdf).

    # 
    for x in header_row.iter('%sth' %br):
        # just look for the para tags - its text is the column header
        if x.find('%spara' %br) is not None:
            col_label = x.find('%spara' %br).text
            field_names.append(col_label)
        else:
            field_names.append("none found")
            pass

    # Some definitions have notes attached in a <notes></notes> tag
    #field_name.append("Notes")
    #print field_names

    return field_names



def parse_row(field_names, row):
    """ Parses the table's tbody tr row, row, for the DICOM Element data
    Returns a list of dicts {header1 : val1, header2 : val2, ...} with each list an Element
    """
    cell_values = []

    # The row should be <tbody><tr>...</tr></tbody> - i.e., this is the body of the table
    # Which leaves the following:
    #   <td><para>Value 1</para></td>
    #   <td><para>Value 2</para></td>
    #   etc...
    # Some rows are
    #   <td><para><emphasis>Value 1</emphasis></para></td>
    #   <td><para><emphasis>Value 2</emphasis></para></td>
    #   etc...
    # There are also some rows that are
    #   <td>
    #       <para>Value 1</para>
    #       <para>Value 2</para>
    #       <note>
    #          <para>Value 3</para>
    #       </note>
    #   </td>
    # There are also some without text values
    #   <td><para/></td>
    #   <td><para><emphasis/></para></td>

    for cell in row.iter('%std' %br):
        for c in cell.iter('%spara' %br):
            #print c.text
            # If we have an emphasis tag under the para tag, skip the line because
            # it's not a line containing a DICOM tag, but an "include table" line
            emph_value = c.find('%semphasis' %br)
            if emph_value is not None or c.text == '':
                cell_values.append("")
            # Otherwise just grab the para tag text
            else:
                if c.text is not None:
                    if ">" == c.text[0]:   #some "Attribute Name" values have ">" as first character
                        cell_values.append(c.text.strip().replace(">", "").replace(u"\u200b", ""))
                    else:
                        cell_values.append(c.text.strip().replace(u"\u200b", ""))
                else:
                    cell_values.append("")


    # Since there are 3 columns, join all the strings that make up the description
    # and notes into a single string
    #print cell_values
    # the rows that start with "Include" are not Tag entries and will be removed by 
    # the clean_attrs function. But first I have to make sure that there are 3 entries
    # so that the values line up correctly with the number of headings in the table (=3)
    if len(cell_values) == 2:
        cell_values.append('')
    cellJoin = join_attr_descr(cell_values)
    return {key : value for key, value in zip(field_names, cellJoin)}



def clean_attrs(attrs):
    # this gets rid of the {'Attribute Name':''} tags that are generated by
    # the lines in the table that start with "Include". I can get rid of the
    # line that has the emphasis (used for italics), but the next link which 
    # is the link for the table to be included I can't get rid of very easily.
    # So cleaning up afterwards is easier.
    attrsClean = [d for d in attrs if d['Attribute Name']!='']

    return attrsClean



def join_attr_descr(cell_values):

    newEntry = []
    newEntry.append(cell_values[0])   # add Attribute Name
    newEntry.append(cell_values[1])   # add Tag 

    # if multiple lines for attribute description, join from end
    # until only 3 [attribute name, tag, attribute description]
    attrDescr = " ".join(cell_values[2:])
    newEntry.append(attrDescr)

    return newEntry
 


def parse_docbook_table(book_root, caption, empty_field_name=""):
    """ Parses the given XML book_root for the table with caption matching caption for DICOM Element data
    Returns a list of dicts with each dict representing the data for an Element from the table
    """
    #br = '{http://docbook.org/ns/docbook}' # Shorthand variable for book_root

    # Find the table in book_root with caption
    for table in book_root.iter('%stable' %br):
        if table.find('%scaption' %br).text == caption:

            # Get the column headers using the above function

            field_names = parse_header(table.find('%sthead' %br).find('%str' %br))

            # Get all the Element data from the table
            attrs = [parse_row(field_names, row) for row in table.find('%stbody' %br).iter('%str' %br)]
            # Get rid of all of the blank entries (the rows that start with "Include")
            attrsClean = clean_attrs(attrs)
            
            return attrsClean
                   
                    
# Program starts here

#global br
br = '{http://docbook.org/ns/docbook}' # Shorthand variable for book_root
attrs = []

# KGH - first look in Part 03 for specific tables (see attrs += statements for table names)
# Next two lines are used to query the online docbook part, which is the latest version
#url = 'http://medical.nema.org/medical/dicom/current/source/docbook/part06/part06.xml'
#response = urllib2.urlopen(url)
fLoc = '/home/karl/Work/INCF/DICOM_docbook_latest/source/docbook/part03/part03.xml'  #KGH
response = open(fLoc)   #KGH - use local copy rather than online version (for now)
tree = ET.parse(response)
root = tree.getroot()
response.close()  # KGH

#patientModules = ["Patient Identification Module Attributes"]

patientModules = ["Patient Relationship Module Attributes", "Patient Identification Module Attributes", "Patient Demographic Module Attributes", "Patient Medical Module Attributes"]

visitModules = ["Visit Relationship Module Attributes", "Visit Identification Module Attributes", "Visit Status Module Attributes", "Visit Admission Module Attributes"]

procedureModules = ["Scheduled Procedure Step Module Attributes", "Requested Procedure Module Attributes", "Imaging Service Request Module Attributes", "Performed Procedure Step Relationship Module Attributes", "Performed Procedure Step Information Module Attributes"]

imagingAcquisitionModules = ["Image Acquisition Results Module Attributes","Billing and Material Management Code Module Attributes", "Instance Availability Notification Module Attributes", "Patient Module Attributes", "Clinical Trial Subject Module Attributes"]

# KGH - get all of the patient modules
for p in patientModules:
    attrs += parse_docbook_table(root, p)

for q in visitModules:
    attrs += parse_docbook_table(root, q)


# KGH - attrs dict now populated; sort by tag value
attrs = sorted(attrs, key=lambda x: x["Tag"])

main_attributes = []
#mask_attributes = []

#KGH -check to see format of attrs key-value pair
#print attrs[0]["Description of Field"]

for attr in attrs:
    group, elem = attr['Tag'][1:-1].split(",")

    # e.g. (FFFE,E000)
    #if attr['VR'] == 'See Note':
    #    attr['VR'] = 'NONE'

    # Convert the micro symbol to "u" for easier handling as string
    # e.g. (0018,1153), (0018,8150) and (0018,8151)
    attr["Attribute Name"] = attr["Attribute Name"].replace(u"µ", "u") # replace micro symbol

    # e.g. (0014,0023) and (0018,9445)
    #if attr['Retired'] in ['RET', 'RET - See Note']:
    #    attr['Retired'] = 'Retired'

    # e.g. (0008,0102), (0014,0025), (0040, A170)
    #if attr['Retired'] in ['DICOS', 'DICONDE', 'See Note']:
    #    attr['Retired'] = ''

    # e.g. (0028,1200)
    #attr['VM'] = attr['VM'].replace(" or ", " ")

    # If blank then add dummy vals
    # e.g. (0018,9445) and (0028,0020)
    #if attr['VR'] == '' and attr['VM'] == '':
    #    attr['VR'] = 'OB'
    #    attr['VM'] = '1'
    #    attr['Name'] = 'Retired-blank'

    # handle retired 'repeating group' tags
    # e.g. (50xx,eeee) or (gggg,31xx)
    #if 'x' in group or 'x' in elem:
    #    attr["Tag"] = group + elem
    #    mask_attributes.append(attr)
    #else:
        #attr["Tag"] = '0x%s%s' %(group, elem)  
    attr["Tag"] = '%s%s' %(group, elem)   #KGH - writing out as 8-characters; don't need 32-bit value
    main_attributes.append(attr)

# write into a file
py_file = file(pydict_filename, "wb")
write_dict(py_file,  main_attributes, tagIsString=False)
py_file.close()

# report back
print ("Finished creating python file %s containing the dicom dictionary" % pydict_filename)
#print ("Wrote %d tags" % (len(main_attributes) + len(mask_attributes)))
print ("Wrote %d tags" % (len(main_attributes)))

#!/usr/bin/python
# -*- coding: utf-8 -*-

# generate_dict_2015b.py

"""
    Reformat a dicom dictionary PS3.6 and PS3.7 docbook xml files (from e.g. standard docs) to Python syntax
    Write the main DICOM dictionary elements as a python dict called main_attributes with format:
    Tag: ('VR', 'VM', "Name", 'is_retired', 'Keyword')
    Where
        Tag is a 32-bit representation of the group, element as 0xggggeeee (e.g. 0x00181600)
        VR is the Value Representation (e.g. 'OB' or 'OB or UI' or 'NONE')
        VM is the Value Multiplicity (e.g. '1' or '2-2n' or '3-n' or '1-32')
        Name is the DICOM Element Name (or Message Field for Command Elements) (e.g. 'Tomo Time' or 'Retired-blank' or 'Time Source')
        is_retired is '' if not retired, 'Retired' otherwise (e.g. '' or 'Retired')
        Keyword is the DICOM Keyword (e.g. 'TomoTime' or 'TimeSource')
    Also write the repeating groups or elements (e.g. group "50xx") as a python dict called
    mask_attributes as masks that can be tested later for tag lookups that didn't work
    using format:
    'Tag': ('VR', 'VM', "Name", 'is_retired', 'Keyword')
    Where
        Tag is a string representation of the element (e.g. '002031xx' or '50xx0022')
"""

# Based on Rickard Holmberg's docbook_to_dict2013.py
# http://code.google.com/r/rickardholmberg-pydicom/
# but rewritten for not using bs4 (and slight change for standard v2015b)

# Based on Rickard Holmberg's generate_dict_2015b.py - found online as part of the "pydicom" package.
# Note that this doesn't grab the definitions - the dictionary in Part 06 doesn't
# include them in the table that I pull info from. This code is used to generate a python 
# dict that contains tags and VR's. I keep the code to get latest docbook from URL, 
# but currently pull from offline/local version of latest docbook so I don't have to be online.
# Also not that this code pulls from the tables in Part 06 and the "Command Fields"
# and "Retired Command Fields" tables in Part 07. Originally, this was written out as two separate
# dictionaries in one named dictionary.  I decided to simplify this to one single dictionary 
# with no name, since I don't need the elements in the 2nd dict.
# K. Helmer
# Massachusetts General Hospital, 2018

import urllib2
import xml.etree.ElementTree as ET
import os

# pydict_filename = '../dicom/_dicom_dict.py'   #this is the filename format expected for pydicom codebase
pydict_filename = 'dicom_dict_vr.dict'  # KGH 
main_dict_name = 'DicomDictionary'   #KGH - not used; only want dict in file, not "name = <dict>"
mask_dict_name = 'RepeatersDictionary'

def write_dict(f, dict_name, attributes, tagIsString):  #KGH-write out the tag as a string in both cases
    if tagIsString:
        #entry_format = """'{Tag}': ('{VR}', '{VM}', '{Name}', '{Retired}', '{Keyword}')"""
        entry_format = """"{Tag}": ("{VR}", "{VM}", "{Name}", "{Retired}", "{Keyword}")"""  #KGH - try double quotes because some Names have apostrophe's in them, e.g., "Referring Physician's Name"
    else:
        #entry_format = """{Tag}: ('{VR}', '{VM}', '{Name}', '{Retired}', '{Keyword}')"""  #original
        #entry_format = """'{Tag}': ('{VR}', '{VM}', '{Name}', '{Retired}', '{Keyword}')""" #KGH - make tag a string
        entry_format = """"{Tag}": ("{VR}", "{VM}", "{Name}", "{Retired}", "{Keyword}")"""  #KGH - try double quotes because some Names have apostrophe's in them, e.g., "Referring Physician's Name"

    #f.write("\n%s = {\n    " % dict_name)
    #f.write("%s = {\n    " % dict_name)   #KGH - no initial newline necessary + don't want "name = {}"
    f.write("{\n    ")      #KGH - just start with dict "{"
    f.write(",\n    ".join(entry_format.format(**attr) for attr in attributes))
    f.write("\n}\n")


def parse_docbook_table(book_root, caption, empty_field_name="Retired"):
    """ Parses the given XML book_root for the table with caption matching caption for DICOM Element data
    Returns a list of dicts with each dict representing the data for an Element from the table
    """

    br = '{http://docbook.org/ns/docbook}' # Shorthand variable for book_root

    # Find the table in book_root with caption
    for table in book_root.iter('%stable' %br):
        if table.find('%scaption' %br).text == caption:

            def parse_header(header_row):
                """ Parses the table's thead/tr row, header_row, for the column headers """
                field_names = []

                # The header_row should be <thead><tr>...</tr></thead>
                # Which leaves the following:
                #   <th><para><emphasis>Header 1</emphasis></para></th>
                #   <th><para><emphasis>Header 2</emphasis></para></th>
                #   etc...
                # Note that for the part06 tables the last col header (Retired) is:
                #   <th><para/></th>
                for x in header_row.iter('%sth' %br):
                    # If there is an emphasis tag under the para tag then its text is the column header
                    if x.find('%spara' %br).find('%semphasis' %br) is not None:
                        col_label = x.find('%spara' %br).find('%semphasis' %br).text
                        field_names.append(col_label)

                    # If there isn't an emphasis tag under the para tag then it must be the Retired header
                    else:
                        field_names.append("Retired")

                return field_names

            # Get the column headers
            field_names = parse_header(table.find('%sthead' %br).find('%str' %br))

            def parse_row(field_names, row):
                """ Parses the table's tbody tr row, row, for the DICOM Element data
                Returns a list of dicts {header1 : val1, header2 : val2, ...} with each list an Element
                """

                cell_values = []

                # The row should be <tbody><tr>...</tr></tbody>
                # Which leaves the following:
                #   <td><para>Value 1</para></td>
                #   <td><para>Value 2</para></td>
                #   etc...
                # Some rows are
                #   <td><para><emphasis>Value 1</emphasis></para></td>
                #   <td><para><emphasis>Value 2</emphasis></para></td>
                #   etc...
                # There are also some without text values
                #   <td><para/></td>
                #   <td><para><emphasis/></para></td>

                for cell in row.iter('%spara' %br):
                    # If we have an emphasis tag under the para tag
                    emph_value = cell.find('%semphasis' %br)
                    if emph_value is not None:
                        # If there is a text value add it, otherwise add ""
                        if emph_value.text is not None:
                            cell_values.append(emph_value.text.strip().replace(u"\u200b", "")) #200b is a zero width space
                        else:
                            cell_values.append("")
                    # Otherwise just grab the para tag text
                    else:
                        if cell.text is not None:
                            cell_values.append(cell.text.strip().replace(u"\u200b", ""))
                        else:
                            cell_values.append("")

                return {key : value for key, value in zip(field_names, cell_values)}

            # Get all the Element data from the table
            attrs = [parse_row(field_names, row) for row in table.find('%stbody' %br).iter('%str' %br)]
            return attrs

attrs = []

# KGH - first look in Part 06 for three specific tables (see attrs += statements for table names)
#url = 'http://medical.nema.org/medical/dicom/current/source/docbook/part06/part06.xml'
#response = urllib2.urlopen(url)
fLoc = '/home/karl/Work/INCF/DICOM_docbook_latest/source/docbook/part06/part06.xml'  #KGH
response = open(fLoc)   #KGH
tree = ET.parse(response)
root = tree.getroot()
response.close()  # KGH

attrs += parse_docbook_table(root, "Registry of DICOM Data Elements")
attrs += parse_docbook_table(root, "Registry of DICOM File Meta Elements")
attrs += parse_docbook_table(root, "Registry of DICOM Directory Structuring Elements")
#KGH ---------------------------------------------------------------

#KGH - Then look at Part 07 that has the command field tables
fLoc = '/home/karl/Work/INCF/DICOM_docbook_latest/source/docbook/part07/part07.xml'  #KGH
response = open(fLoc)   #KGH
#url = 'http://medical.nema.org/medical/dicom/current/source/docbook/part07/part07.xml'
#response = urllib2.urlopen(url)
tree = ET.parse(response)
root = tree.getroot()

command_attrs = parse_docbook_table(root, "Command Fields") # Changed from 2013 standard
for attr in command_attrs:
    attr["Name"] = attr["Message Field"]
    attr["Retired"] = ""

retired_command_attrs = parse_docbook_table(root, "Retired Command Fields")
for attr in retired_command_attrs:
    attr["Name"] = attr["Message Field"]
    attr["Retired"] = "Retired"

attrs += command_attrs
attrs += retired_command_attrs
#KGH -------------------------------------------------------------------------------


# KGH - attrs dict now populated; sort by tag value
attrs = sorted(attrs, key=lambda x: x["Tag"])

main_attributes = []
mask_attributes = []

#KGH -check to see format of attrs key-value pair
#print attrs[0]["Description of Field"]

for attr in attrs:
    group, elem = attr['Tag'][1:-1].split(",")

    #KGH - unused as tables in Part 06 doesn't include definitions in tables
    #KGH check to see if Description of Field exists; if not create key and make value a blank string
    #if 'Description of Field' in attr:
    #    pass
    #else:
    #    attr['Description of Field'] = 'None'

    # e.g. (FFFE,E000)
    if attr['VR'] == 'See Note':
        attr['VR'] = 'NONE'

    # e.g. (0018,1153), (0018,8150) and (0018,8151)
    attr["Name"] = attr["Name"].replace(u"µ", "u") # replace micro symbol

    # e.g. (0014,0023) and (0018,9445)
    if attr['Retired'] in ['RET', 'RET - See Note']:
        attr['Retired'] = 'Retired'

    # e.g. (0008,0102), (0014,0025), (0040, A170)
    if attr['Retired'] in ['DICOS', 'DICONDE', 'See Note']:
        attr['Retired'] = ''

    # e.g. (0028,1200)
    attr['VM'] = attr['VM'].replace(" or ", " ")

    # If blank then add dummy vals
    # e.g. (0018,9445) and (0028,0020)
    if attr['VR'] == '' and attr['VM'] == '':
        attr['VR'] = 'OB'
        attr['VM'] = '1'
        attr['Name'] = 'Retired-blank'

    # handle retired 'repeating group' tags
    # e.g. (50xx,eeee) or (gggg,31xx)
    if 'x' in group or 'x' in elem:
        attr["Tag"] = group + elem
        mask_attributes.append(attr)
    else:
        #attr["Tag"] = '0x%s%s' %(group, elem)  
        attr["Tag"] = '%s%s' %(group, elem)   #KGH - writing out as string; don't need 32-bit value
        main_attributes.append(attr)

py_file = file(pydict_filename, "wb")
#KGH - the following 3 write lines are for pydicom only and not needed for NIDM
#py_file.write("# %s\n" % os.path.basename(pydict_filename))
#py_file.write('"""DICOM data dictionary auto-generated by %s"""\n' % os.path.basename(__file__))
#py_file.write('from __future__ import absolute_import\n')
write_dict(py_file, main_dict_name, main_attributes, tagIsString=False)
#write_dict(py_file, mask_dict_name, mask_attributes, tagIsString=True)

py_file.close()

print ("Finished creating python file %s containing the dicom dictionary" % pydict_filename)
print ("Wrote %d tags" % (len(main_attributes) + len(mask_attributes)))

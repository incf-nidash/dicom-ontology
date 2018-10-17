#!/usr/bin/python
# -*- coding: utf-8 -*-

# generate_dict_2015b.py
# Note that utf-8 encoding above just serves to insert non-ascii chars into the code,
# but doesn't do anything for de/encoding
"""
    Original:
    Reformat a dicom dictionary PS06 and etc docbook xml files (from e.g. standard docs) to Python syntax
    Write the main DICOM dictionary elements as a python dict called main_attributes with format:
    Tag: ('Attribute Name', 'Attribute Description')
    Where
        Tag is a string representation of the (group, element) as "ggggeeee" (e.g. 00181600)
        Attribute Name is the Tag label
        Attribute Description is the Tag defnition
"""
"""
Original:
Based on Rickard Holmberg's docbook_to_dict2013.py
http://code.google.com/r/rickardholmberg-pydicom/
but rewritten for not using bs4 (and slight change for standard v2015b)

- Based on Rickard Holmberg's generate_dict_2015b.py - found online as part of the 
  "pydicom" package - though almost completely rewritten here .
- Modified that code to get a table with the tags and VR values = vr_generate_dict.py
- This code starts from vr_generate_dict.py and adds code to extract definitions from  
  tables (that sadly don't include the VR values). This code is used to generate a python 
  dict that contains Tags, Attribute Names, Attribute Descriptions and potentially Type. 
  I keep the code to get the latest docbook from URL, but currently pull from an 
  offline/local version of so I don't have to be online.
- This writes out the table rows as a single dictionary. 
- Generalize the code to go through all of the tables in the document so I don't 
  have to enter each table name in a list that is then looped over (though I do
  have to create a list of Tables to skip because their formats make it difficult
  to weed out through code).
Karl G. Helmer
Massachusetts General Hospital, 2018
"""

import urllib2
import xml.etree.ElementTree as ET
import os, io

pydict_filename = 'dicom_dict_def.dict'  


def parse_header(header_row):
    """ Parses the table's thead/tr row, header_row, for the column headers

    The header_row should be <thead><tr>...</tr></thead>
    Which leaves the following:
    In the Part 06 and Part 07 sections docbook tables use:
      <th><para><emphasis>Header 1</emphasis></para></th>
      <th><para><emphasis>Header 2</emphasis></para></th>
      etc...
    But in Part 03 the <emphasis> tag is not used.  This means that we have:
      <th><para>Header 1</para></th>
      <th><para>Header 2</para></th>
      inside the <thead></thead> block
    so each para element inside <thead> is the column heading
    (although it looks as though the table column headings are still bold
    when displayed in the pdf).
    """

    field_names = []

    for x in header_row.iter('%sth' %br):
        # just look for the para tags - its text is the column header
        if x.find('%spara' %br) is not None:
            col_label = x.find('%spara' %br).text
            field_names.append(col_label)
        else:
            field_names.append("none found")
            pass

    return field_names



def parse_row(field_names, row):
    """ Parses the table's tbody tr row, row, for the DICOM Element data
    Returns a list of dicts {header1 : val1, header2 : val2, ...} with each list an Element

    The row should be <tbody><tr>...</tr></tbody> - i.e., this is the body of the table
    Which leaves the following:
      <td><para>Value 1</para></td>
      <td><para>Value 2</para></td>
      etc...
    Some rows are
      <td><para><emphasis>Value 1</emphasis></para></td>
      <td><para><emphasis>Value 2</emphasis></para></td>
      etc...
    There are also some rows that are
      <td>
          <para>Value 1</para>
          <para>Value 2</para>
          <note>
             <para>Value 3</para>
          </note>
      </td>
    There are also some without text values
      <td><para/></td>
      <td><para><emphasis/></para></td>
    """

    cell_values = []

    for cell in row.iter('%std' %br):
        for c in cell.iter('%spara' %br):
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


    # Join all the strings that make up the description and notes into a single string
    # the rows that are in italics are not Tag entries and will be removed by 
    # the clean_attrs function. But first I have to make sure that there are the same 
    # number of entries as columns so that the values line up correctly
    tableCols = len(field_names)
    numValues = len(cell_values)
    if numValues < tableCols:
        for k in range(tableCols - numValues):
            cell_values.append('')

    cellJoin = join_attr_descr(cell_values, field_names)
    return {key : value for key, value in zip(field_names, cellJoin)}



def clean_attrs(attrs):
    """
    This gets rid of the entries with {'Attribute Name':''} tags that are generated by
    the lines in the table that start with "Include". I can get rid of the
    line that has the emphasis (used for italics), but the next link which 
    is the link for the table to be included I can't get rid of very easily other
    than through this method. Also, a number of Tables have Key rather than Attribute 
    Name, so it's easier to clean up after the inital run through the entries.
    Remove those entries that don't have a definition.  
    """
    attrs1 = []
    attrs2 = []
    attrs3 = []
    #now make sure that the Tag value starts with a '(' and not, for example "See"
    for d in attrs:
        if '(' in d['Tag']:   # get rid of those without a valid Tag
            temp = d['Tag']
            if temp[0] == '(':
                attrs1.append(d)
            else:
                pass

    #first make sure that the Attribute Name or Key has a value
    #these can be in the same loop since they don't appear in the 
    #same entry.
    for d in attrs1:
        if "Attribute Name" in d:  # keep those with an Attribute Name
            if d["Attribute Name"] != '':
                attrs2.append(d)
            else:
                pass

    for d in attrs1:
        if "Key" in d:    # keep those with a Key (d's that don't have Attr Name, but Key)
            if d["Key"] != '':
                attrs2.append(d)
            else:
                pass

    #weed out those entries that are missing a definition/description
    for d in attrs2:
        if "Description" in d:    # keep those with an Description
            if d["Description"] != '':
                attrs3.append(d)
            else:
                pass

    for d in attrs2:
        if "Attribute Description" in d:    # keep those with an Attribute Description
            if d["Attribute Description"] != '':
                attrs3.append(d)
            else:
                pass

    return attrs3



def remove_duplicates(attrs):
    ''' This removes duplicate entries from the final list of entries.
    Note that duplicate means that the entire entry is the same. The 
    tags with different definitions will be kept.
    '''
    b = []
    b = [i for n, i in enumerate(attrs) if i not in attrs[n+1:]]
    
    return b



def join_attr_descr(cell_values, field_names):
    """ 
    Table headings are Attribute Name, Tag, [Type], Attribute Description; 
    and may or may not have Type column. I am also including <note> entries
    with the Descriptions. Attribute Descriptions + notes may be over multiple 
    <para> so have to join them to get a single string.
    """
    newEntry = []
    tableCols = len(field_names)

    # append from front items that are in a single <para>
    for i in range(tableCols-1):
        newEntry.append(cell_values[i])

    # now get Attribute Description, which may be multiple lines and includes 
    # <note> entries; join from end 
    attrDescr = " ".join(cell_values[(tableCols-1):])
    newEntry.append(attrDescr)

    return newEntry
 


def parse_docbook_table(book_root):
    """ Parses the given XML book_root for the table with caption matching caption for DICOM Element data
    Returns a list of dicts with each dict representing the data for an Element from the table
    """
    #br = '{http://docbook.org/ns/docbook}' # Shorthand variable for book_root
    attrsAll = []
    attrsRow = []
    skipTables = ["Compressed Palette Color Lookup Table Data", "Segment Types", "Discrete Segment Type", \
                  "Linear Segment Type", "Indirect Segment Type", "Whole Slide Microscopy Image Flavors", \
                  "Whole Slide Microscopy Image Derived Pixels", "Types of Positioner and Detector Motion", \
                  "Defined Terms for Printer and Execution Status Info", "Content Assessment Results Directory Record Results Keys"]

    # Find the table in book_root with caption
    for table in book_root.iter('%stable' %br):
        caption = table.find('%scaption' %br).text
        #if table.find('%scaption' %br).text == caption:  #from when I had a list of captions to loop through
         #make sure there is a caption; otherwise probably a retired module + check if in list of tables to be skipped
        if caption and (caption not in skipTables):   
            if not "Example" in caption:
                # Get the column headers using the above function
                field_names = parse_header(table.find('%sthead' %br).find('%str' %br))
                # Get the row values from the table; make sure it has a Tag and Description
                if ("Tag" in field_names) and ("Key" or "Attribute Description" or "Description" in field_names):
                    # Get all the Element data from the table
                    attrsRow = [parse_row(field_names, row) for row in table.find('%stbody' %br).iter('%str' %br)]
                    attrsAll.append(attrsRow)   #since now looping through all tables have to collect attrs inside this module
                else:
                    pass    # if no Key, Tag or Description
            else:
                pass    # skip if an Example
        else:
            #print "no caption or a skipped Table"
            pass    # if there is no caption then skip; retired module

    # now have to flatten the list of lists (of dictionaries) into a list of dictionaries
    attrsAllFlat = [item for sublist in attrsAll for item in sublist]
                   
    return attrsAllFlat


def write_dict(f, entries): 
    ''' The XML parsing module works with utf-8, but f.write assumes ascii so I 
        have to specifically encode the write to be in utf-8 otherwise it chokes
        on tags like (0018,1136) that has unicode for the angular degree symbol.
        If I encode as utf-8 the symbol is written instead of something like \xb0.
    '''
    f.write("{\n    ")      #just start with dict: "{"
    for entry in entries:
        print entry

        if "Type" in entry:
            #.encode('utf-8')
            if "Description" in entry:
                f.write(",\n    "+""""{0}": ("{1}", "{2}", "{3}")""".format(entry["Tag"], entry["Attribute Name"].encode('utf-8'), entry["Description"].encode('utf-8'), entry["Type"]))
            elif "Attribute Name" in entry:
                f.write(",\n    "+""""{0}": ("{1}", "{2}", "{3}")""".format(entry["Tag"], entry["Attribute Name"].encode('utf-8'), entry["Attribute Description"].encode('utf-8'), entry["Type"]))
            elif "Key" in entry: 
                f.write(",\n    "+""""{0}": ("{1}", "{2}", "{3}")""".format(entry["Tag"], entry["Key"].encode('utf-8'), entry["Attribute Description"].encode('utf-8'), entry["Type"]))
            else:
                print "has Type, but not any of specified key collections"
        else:
            if "Description" in entry:
                f.write(",\n    "+""""{0}": ("{1}", "{2}")""".format(entry["Tag"], entry["Attribute Name"].encode('utf-8'), entry["Description"].encode('utf-8')))
            elif "Attribute Description" in entry:
                f.write(",\n    "+""""{0}": ("{1}", "{2}")""".format(entry["Tag"], entry["Attribute Name"].encode('utf-8'), entry["Attribute Description"].encode('utf-8')))
            else:
                print "Entry not in any known format"
        #f.write(",\n    ".join(entry_format.format(**attr) for attr in attributes)) #orig version
    f.write("\n}\n") # ending "}"



# Program starts here

#global br
br = '{http://docbook.org/ns/docbook}' # Shorthand variable for book_root
attrs = []
main_attributes = []

# Run on DICOM Part 03 and look for Tables that have Tags and Definitions
# Next two lines are used to query the online docbook part, which is the latest version
#url = 'http://medical.nema.org/medical/dicom/current/source/docbook/part06/part06.xml'
#response = urllib2.urlopen(url)
# But here I use the offline version so I don't have to be online
fLoc = '/home/karl/Work/INCF/DICOM_docbook_latest/source/docbook/part03/part03.xml' 
response = open(fLoc)
tree = ET.parse(response)
root = tree.getroot()
response.close()  


# There are too many in Part 03 to list so loop through and weed out
#for p in patientModules:
#    attrs += parse_docbook_table(root, p)

# parse each table in selected docbook Part rather than looping through a list of Tables
attrs = parse_docbook_table(root)

# Remove entries that have blank fields or that have a bad Tag
attrsClean = clean_attrs(attrs)
# Remove entries in which all fields are the same
attrsNoDuplicates = remove_duplicates(attrsClean)

# attrs dict now populated; sort by tag value
attrsSort = sorted(attrsNoDuplicates, key=lambda x: x["Tag"])

for a in attrsSort:
    group, elem = a['Tag'][1:-1].split(",")

    # Convert the micro symbol to "u" for easier handling as string  #original, but we want units so utf-8
    # e.g. (0018,1153), (0018,8150) and (0018,8151)
    #attr["Attribute Name"] = attr["Attribute Name"].replace(u"µ", "u") # replace micro symbol

    # handle retired 'repeating group' tags
    # e.g. (50xx,eeee) or (gggg,31xx)
    #if 'x' in group or 'x' in elem:
    #    attr["Tag"] = group + elem
    #    mask_attributes.append(attr)
    #else:
        #attr["Tag"] = '0x%s%s' %(group, elem)  
    a["Tag"] = '{g}{e}'.format(g=group,e=elem)   #writing out as 8-characters; don't need 32-bit value

# write into a file
py_file = file(pydict_filename, "wb")
write_dict(py_file, attrsSort)
py_file.close()

# report back
print ("Finished creating python file %s containing the dicom dictionary" % pydict_filename)
print ("Wrote %d tags" % (len(attrsSort)))

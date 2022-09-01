#!/usr/bin/env python3

import argparse
import xml.etree.ElementTree as ET

def main():
    # Get the command line arguments from the user.
    parser = argparse.ArgumentParser(
        description='A script to parse and add temporary junit test files to an aggregate one.')
    parser.add_argument('-t', '--temp', metavar='temp', type=str,
        required=True,
        help='the path of the temporary xml file')
    parser.add_argument('-a', '--agg', metavar='aggregate', type=str,
        required=True,
        help='the path of the aggregate xml file')

    # Parse arguments.
    args = parser.parse_args()
    temp = args.temp
    agg = args.agg

    parseXML(temp, agg)

    return

def parseXML(temp, agg):

    # create element tree object
    temp_tree = ET.parse(temp)
    agg_tree = ET.parse(agg)

    # get root element
    temp_root = temp_tree.getroot()
    agg_root = agg_tree.getroot()

    #print(ET.tostring(temp_root))
    #print(ET.tostring(agg_root))

    for child in temp_root: #testsuite in temp_root.findall("./testsuites"):
        agg_root.append(child)

    agg_tree.write(agg, encoding='UTF-8', xml_declaration=True)
    
    return

if __name__ == "__main__":
    main()

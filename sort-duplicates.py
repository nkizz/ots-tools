# Copyright (C) 2016 Open Tech Strategies, LLC
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

# This script takes an XML file generated by the CPD utility of PMD (see
# github.com/pmd/pmd) and relative path to the directory that CPD was
# run on.  It returns a list of duplicated files, sorted by their degree
# of similarity.
# 
# Ultimately it may also return a list of duplicated classes
# 
# Usage example:
# 
# $ python sort-duplicates.py <xml file to parse> <path to coeci-cms-mpsp tree, not including coeci-cms-mpsp>
#

import xml.etree.ElementTree as Tree
import sys


# with thanks to:
# http://stackoverflow.com/questions/845058/how-to-get-line-count-cheaply-in-python,
# this counts the lines in a file:
def file_len(fname):
    with open(fname) as f:
        for i, l in enumerate(f):
            pass
    return i + 1


# Takes a set of pre-parsed elements from an xml file and returns a list
# of lists.
# Combines the number of lines duplicated in a pair of files so that the
# ultimate percentage represents the total duplication across files,
# rather than the percentage duplicated in each chunk.
# Returns a list of lists with [total lines duplicated, file path 1,
# file path 2]
def total_duplication(xml_root):
    reduced_filelist = []
    for filepair in xml_root:
        # find the filenames
        filepath1 = filepair._children[0].attrib['path']
        # Chop off the first part, up to "coeci-cms-mpsp." This is
        # an artifact of my particular CPD-generated XML file, so others
        # might not need to do this split.
        filepath1 = filepath1.split('../../../')[1]
        filepath2 = filepair._children[1].attrib['path']
        filepath2 = filepath2.split('../../../')[1]
        # get the size of the duplication ("lines")
        dupe_size = filepair.attrib['lines']

        # If both files already exist as a pair in the reduced_filelist
        # array then add the dupe_size to their existing dupe element
        # and do not add them to reduced_filelist.  Otherwise add them
        # as a new list in reduced_filelist.
        include_pair = True
        for pair in reduced_filelist:
            if (pair[1] == filepath1) and (pair[2] == filepath2):
                #print("Found one:")
                #print("First file is " + pair[1] + " or " + filepath1)
                #print("Second file is " + pair[2] + " or " + filepath2)
                # update dupe size
                #print("Size of duplication chunk is " + dupe_size)
                pair[0] = int(pair[0]) + int(dupe_size)
                #print("Total duplication becomes " + str(pair[0]))
                # don't include it in reduced list
                include_pair = False
                break

        if include_pair:
            reduced_filelist.append([dupe_size, filepath1, filepath2])
        
        
    return reduced_filelist


# Takes a list of lists, alters it, and returns it.  Each returned list
# contains: 
# - number of lines duplicated
# - number of lines in first file
# - abbreviated path to first file
# - number of lines in second file
# - abbreviated path to second file
def find_filesizes(filelist):
    filesizes_array = []
    
    # for each `duplication` block in the xml file:
    for filepair in filelist:
        # get the number of lines of each file
        try:
            filesize1 = file_len(sys.argv[2] + filepair[1])
            filesize2 = file_len(sys.argv[2] + filepair[2])
        except IndexError:
            print("Please provide the path to 'coeci-cms-mpsp'.")
            return None
        filesizes_array.append([filepair[0], filesize1, filepair[1], filesize2, filepair[2]])

    return filesizes_array


# Returns an array that consists of:
#  - percentage of lines of file 1 duplicated
#  - name of file 1
#  - percentage of lines of file 2 duplicated
#  - name of file 2
#  - number of lines duplicated
def percentage_duplicated(size_array):
    percent_array = []
    for arr in size_array:
        dupe = int(arr[0])
        percent1 = round(float(dupe)/float(arr[1]), 2)
        percent2 = round(float(dupe)/float(arr[3]), 2)
        percent_array.append([percent1, arr[2], percent2, arr[4], arr[0]])

    return percent_array



# Returns a list of filename pairs, with their percentage duplicated,
# sorted from highest duplicate percentage to lowest (for the first file
# of the pair).
def sort_files(percent_array):
    # Thanks to https://wiki.python.org/moin/HowTo/Sorting
    sorted_array = sorted(percent_array, key=lambda array: array[0]) 
    return sorted_array


# Print the files with the percentage that they are duplicated to
# stdout.
# Takes an array with the following elements: percentage of first file
# duplicated, first file name, percentage of second file duplicated,
# second file name, total lines duplicated.
def prettyprint_filelist(files):
    for duped_file in files:
        print("PAIR: " + str(duped_file[4]) +  " lines in common:")
        print("  " + str(duped_file[0]*100) + "% of " + duped_file[1])
        print("  " + str(duped_file[2]*100) + "% of " + duped_file[3])
        print("\n")
    return


# Parses command line arguments (an XML file and a path to the top-level
# dir where the files referenced in that XML file reside), and returns a
# sorted list of the most-heavily-duplicated files.
def main():
    try:
        tree = Tree.parse(sys.argv[1])
        root = tree.getroot()
    except IndexError:
        print("Please provide an xml file.")
        return None

    # Combine all the duplicated sections of a file to get total
    # duplicated percentage
    shorter_filelist = total_duplication(root)
    array_of_sizes = find_filesizes(shorter_filelist)
    # compare the size of the file(s) to the size of the duplication
    try:
        array_of_percents = percentage_duplicated(array_of_sizes)
    except TypeError:
        return None
    
    # sort output based on the result of that comparison
    file_list = sort_files(array_of_percents)

    # display sorted list to user
    prettyprint_filelist(file_list)
    return

main()

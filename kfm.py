import itertools
from collections.abc import Mapping
from pathlib import Path
import re
from datetime import datetime
import argparse
import yaml
import json


class IncorrectWellSpec(RuntimeError):
    '''
    Runtime error thrown when well specification is out of order (e.g. 'A12-A03' or isn't an avail option e.g.'A1-A20')
    '''


class WellNotFound(RuntimeError):
    '''
    Runtime error thrown when well does not map to a Keyence XY# folder')
    '''


class IncorrectGroupbyError(RuntimeError):
    '''
    Runtime error thrown when groupby option isn't one of avail options ['none', 'XY', 'T', 'stitch', 'Z', 'CH'] or the option ['none'] is provided with other groupby args
    '''


class DestExistsError(RuntimeError):
    '''
    Runtime error thrown when trying to move a file to a destination that already contains a file with the same name
    '''


class RecordExistsError(RuntimeError):
    '''
    Runtime error thrown when trying to move when record still exists - should reverse move first before attempting more moves
    '''

class RecordDoesNotExistsError(RuntimeError):
    '''
    Runtime error thrown when trying to reverse move but record doesn't exists in the working directory
    '''


def matchImgType(path):
    """
    Given path to group folder, determine image type for the group folder
    """

    # Just check using first tif file found
    for f in path.rglob('*.tif'):
        isTimelapse = True if (re.search(r'_T(\d+)_', f.name) != None) else False
        isZstack = True if (re.search(r'_Z(\d+)_', f.name) != None) else False
        isStitch = True if (re.search(r'_(\d{5})_', f.name) != None) else False
        break

    img_type = {'isZstack': isZstack, 'isTimelapse': isTimelapse, 'isStitch': isStitch}

    # Make regex pattern where naming system is 'prefix_Timelapse_XY_Stitch_Zstack_Channel.tif'
    pattern = r'(?P<prefix>\w+)'
    if img_type['isTimelapse']:
        pattern += r'_(?P<T>T{1}\d+)'
    pattern += r'_XY(?P<XY>\d+)'
    if img_type['isStitch']:
        pattern += r'_(?P<stitch>\d{5})'
    if img_type['isZstack']:
        pattern += r'_(?P<Z>Z{1}\d+)'
    pattern += r'_(?P<CH>.*).tif'
    
    return (img_type, pattern)

def mapXYtoWell(path):
    """
    Given path to group folder, map XY## to wells using the shortcuts left by Keyence
    """
    # Define dicts to help account keep track of wells and duplicates in wells
    XYtoWell = dict()          # e.g. {'XY01':'A01', 'XY02':'A01'}
    welltoXY_unique = dict()
    XYtoWell_unique = dict()   # e.g. {'XY01':'A01(1)', 'XY02':'A01(2)'}
    well_list = list()
    duplicates = dict()        # e.g. {'A01':2}

    # Find each XY##/_WELL shortcut folder
    for f in path.glob(r'*XY*/_*'):

        well = f.name[1:]  # ignore '_' that precedes each well shortcut
        XY = f.parent.name

        # if well is not unique, update new and old well names to avoid duplicate
        # e.g. A01 becomes A01(1) and new well becomes A01(2)
        if well in well_list:
            # If 1st duplicate
            if well not in duplicates:
                # Add existing entry to unique mapping as (1)
                XYtoWell_unique[welltoXY_unique[well]] = well+'(1)'
                # Add dup. entry to unique mapping as (2) then change dup count to 2
                XYtoWell_unique[XY] = (well+'(2)')
                duplicates[well] = 2
            else:
                duplicates[well] += 1
                XYtoWell_unique[XY] = '{}({})'.format(well, duplicates[well])
        # Otherwise well is unique
        else:
            # Add it as a unique well and to the welltoXy mapping
            XYtoWell_unique[XY] = well
            welltoXY_unique[well] = XY
            well_list.append(well)

        # Regardless if dupl or not, add XY to well mapping b/c that will always be unique (all XYs are unique)
        XYtoWell[XY] = well
    
    
    return (XYtoWell, XYtoWell_unique)

def getGroupbyPath(path, groupby, img_type, well_info, uniq_well_ID, match):
    '''
    Determine the path of where things will be moved depending on the groupby options
    '''

    # Create path depending on groupby options
    # groupby_opt = ['none', 'natural', 'XY', 'cond', 'T', 'stitch', 'Z', 'CH']

    # If none, don't specify any subdirectories b/c all will be dumped into the provided group_folder path
    if groupby[0] == 'none':
        dest = path
    # If natural grouping, then group by condition/XY/stitch(opt)/Z(opt)/CH so you can easily scroll 
    # thru images for a condition>in a well>at the same location>for a single channel or overlay
    elif groupby[0] == 'natural':
        # Condition/XY folders
        dest = path / well_info / (uniq_well_ID+'_'+well_info)
        if img_type['isStitch']:
            if img_type['isZstack']:
                dest = dest / ('stitch' + match.group('stitch')) / match.group('Z') / match.group('CH')
            else:
                dest = dest / ('stitch' + match.group('stitch')) / match.group('CH')
        else:
            if img_type['isZstack']:
                dest = dest / match.group('Z') / match.group('CH')
            else:
                dest = dest / match.group('CH')
    else:
        # For all other options: ['XY', 'cond', 'T', 'stitch', 'Z', 'CH']
        # Just order in terms of what how the user specified
        dest = path
        for group_name in groupby:
            # If cond replace with well info
            if group_name == 'cond':
                dest = dest / well_info
            # If XY replace with unique well ID (e.g. A01(2))
            elif group_name == 'XY':
                dest = dest / (uniq_well_ID+'_'+well_info)
            # Otherwise replace with T#, stitch#, or Z#
            else:
                dest = dest / (group_name + match.group(group_name))

    # Return destination path
    return dest

def rmkdir(dest, new_dirs):
    '''
    Recursively make new directories as needed so parents are created first then children and are noted in 
    new_dirs to make reversing moves easier
    '''

    # Recursively make parent directories if necessary
    if not dest.parent.exists():
        rmkdir(dest.parent, new_dirs)

    # Make dest dir
    dest.mkdir()
    # Note what directories were made during the move so if move is reversed
    # children can be deleted before parent directories
    new_dirs.append(str(dest))
    
    return 

def moveFiles(path, wellMap, groupby=['natural']):
    '''
    Main functiont that moves files. Default is grouping by 'natural' where all images get put in the natural ordering of:
    

    Args:
    -----
    path: A path pointing to the group folder path (keyence naming system)
    wellMap: A dict mapping wells to conditions, e.g. {'A01': ['dsRed', 'None'], 'A02': ['dsRed', '6F']}
    groupby: A list of how to group images where order dictates order of subdirectories 
             (e.g. groupby=['XY', 'Z'] groups into group_folder_path/XY/Z).
    '''

    # All ways to group images
    groupby_opt = ['none', 'XY', 'cond', 'T', 'stitch', 'Z', 'CH', 'natural']
    # Determine image type and patttern for regex matching
    (img_type, pattern) = matchImgType(path)

    # Check if user provided groupby option is correct and this is a new move (e.g. no record.txt exists)
    try:
        # Check if user provided groupby option is one of the avail options
        for group in groupby:
            if group not in groupby_opt:
                raise(IncorrectGroupbyError(
                    'Cannot group by \'{}\', select from: {}'.format(group, groupby_opt)))
            if group == 'T' and not img_type['isStitch']:
                raise(IncorrectGroupbyError(
                    'Cannot group by \'{}\' because not timelapse image'.format(group)))
            if group == 'stitch' and not img_type['isTimelapse']:
                raise(IncorrectGroupbyError(
                    'Cannot group by \'{}\' because not stitch image'.format(group)))
            if group == 'Z' and not img_type['isZstack']:
                raise(IncorrectGroupbyError(
                    'Cannot group by \'{}\' because not Z stack image'.format(group)))
        
        # Check if user provided groupby is just 'none or 'natural' that it's the only option provided 
        if ('none' in groupby or 'natural' in groupby) and len(groupby) != 1:
            raise(IncorrectGroupbyError(
                'If \'none\' or \'natural\' option is selected, you cannot group by any other options.')
            )
        
        # Check if record.txt exists in the current group folder - if it has the whole move should be completely reversed before attempting new moves
        if (path/'record.txt').exists():
            raise RecordExistsError(
                'Files have already been moved. Reverse the move before trying to move files again.')
            
    except RuntimeError as error:
        print('Error: ' + repr(error))
        return

    # Create a record list to store where files were moved in format of (oldpath, newpath)
    record = list()
    # Create a directory list to store what new directories were made
    new_dirs = list()
    # Create a directory list to store what files weren't moved
    unmoved_list = list()

    # Deal with everything that's not a .tif by moving it into a 'unmoved' folder
    # note - don't need to do recursively b/c everything that's left behind in the group folder 
    #        will get moved at top subdirectory level
    dest = path / 'unmoved'
    for f in path.glob('*'):
        # Skip if .DS_Store file in macs
        if f.name == '.DS_Store':
            continue
        unmoved_list.append((str(f), str(dest/f.name)))
    dest.mkdir()
    new_dirs.append(str(dest))


    # Map each XY to a well, e.g. XY01 is A01
    (XYtoWell, XYtoWell_unique) = mapXYtoWell(path)
    # Recursively go thru all tif files in specified group folder path
    for f in path.rglob('*.tif'):

        # Extract metadata from img titles
        match = re.search(pattern, f.name)

        # Get well ID (e.g. A01) and well info (e.g. 6FDDRR)
        well_ID = XYtoWell['XY'+match.group('XY')]  # e.g. A01
        uniq_well_ID = XYtoWell_unique['XY' +
                                        match.group('XY')]  # e.g. A01(2)

        if well_ID not in wellMap:
            raise WellNotFound('{} not found in well mapping. Make sure {} has a specified condition'.format(well_ID, well_ID))

        # Create path depending on groupby options
        dest = getGroupbyPath(path, groupby, img_type,
                              wellMap[well_ID], uniq_well_ID, match)

        # Make new directories for the new groupby options if necessary
        if not dest.exists():
            rmkdir(dest, new_dirs)

        # Sub XY## in pic name with the well ID and info (e.g. A01(2)_6FDD)
        newFileName = re.sub(r'(XY\d+)', uniq_well_ID+'_'+wellMap[well_ID], f.name)
        dest = dest / newFileName

        # Record where file will be moved in order of (oldPath, newPath)
        record.append((str(f), str(dest)))

    # Record where files are getting moved in order of 1. unmoved files 2. tif files 3. any new directories made
    # This makes reversing moves easier b/c unmoved files include top level subdirectories that must be moved first
    # before any .tif files are moved (e.g. can't move .tif into path/XY01 if path/XY01 is now in path/misc/XY01)
    with open(path/'record.json', mode='w') as fid:
    
        json.dump({
            'record_time': datetime.now().strftime('%Y.%m.%d_%H.%M.%S'),
            'unmoved_list': unmoved_list, 
            'record': record,
            'new_dirs': new_dirs}, fid)

    # Actually move tif files
    for rec in record:
        src = Path(rec[0])
        dest = Path(rec[1])

        if not dest.exists():
            src.replace(dest)
        else:
            raise(
                DestExistsError('\' {} \' could not be moved, destination already exists'.format(dest))
            )
        
    # Actually move everything else
    for rec in unmoved_list:
        src = Path(rec[0])
        dest = Path(rec[1])

        if not dest.exists():
            src.replace(dest)
        else:
            raise(
                DestExistsError(
                    '\' {} \' could not be moved, destination already exists'.format(dest))
            )
     
def revMoveFiles(path):
    '''
    Reverse the file move using history recorded in record.json

    Args:
    -----
    path: A path pointing to directory that has record.json which stores where files got moved to
    '''

    if not (path/'record.json').exists():
        raise RecordDoesNotExistsError('record.txt not found in current working directory')
        
    new_dir_list = list()

    with open(path/'record.json', mode='r') as file:

        # Load json data for reversing the move
        rev_data = json.load(file)

        # For the unmoved and record files, simply reverse the move
        for rec in rev_data['unmoved_list']+rev_data['record']:

            dest = Path(rec[0])
            src = Path(rec[1])

            # If destination file doesn't exist, move it
            if not dest.exists():
                src.replace(dest)
            else:
                raise(
                    DestExistsError(
                        '\' {} \' could not be moved, destination already exists'.format(dest))
                )
        
        # Load and sort new_dir_list by rev length so subdirectories will be deleted before parent ones
        new_dir_list = rev_data['new_dirs']
        new_dir_list.sort(key=len, reverse=True)
        for newdir in new_dir_list:
            # Check if newdir is empty (size 64)
            newdir = Path(newdir)
            # If not - try removing hidden .DS_Store file for Macs
            if newdir.stat().st_size != 64:
                (newdir/'.DS_Store').unlink()
            Path(newdir).rmdir()

    # Print success msg
    print('Move successfully reversed at {}'.format(rev_data['record_time']))
    # Rename record.txt file
    (path/'record.json').rename(path/('{}_rev_{}'.format(rev_data['record_time'], 'record.json')))

def convWelltoCoord(well):
    '''
    Given well in string format (e.g. 'A01' or 'A1'), convert to a coordinate (row, col) where 'A1'=(0,0) and B12=(1,11).
    Will only accept max size of a 96-well, e.g. A01 to H12

    Args:
    -----
    well: a string representation of the well, e.g. 'A01' or 'A1' or 'a1'
    '''
    row_letters = 'ABCDEFGH'
    well_letToNum = {let: i for (i, let) in enumerate(row_letters)}


    # Grab info from well rect spec
    match = re.match('(?P<well_let>[a-zA-Z]{1})(?P<well_num>[\d]{1,})', well)
    well_let = match.group('well_let').capitalize()
    well_num = int(match.group('well_num'))

    # Check if w/in limits of 96-well
    if well_let not in well_letToNum:
        raise IncorrectWellSpec('Well row must be either in ' + row_letters)
    if well_num > 12 or well_num < 1:
        raise IncorrectWellSpec('Well col must be from 1-12')
    
    
    # return coord in order (row, col)
    return (well_letToNum[well_let], well_num-1)

def convPlateToWellMap(plate):
    '''
    Given plate , give back dictionary mapping where plate[0][0] = ['dsRed', '6F'] gives back {'A01': ['dsRed', '6F']}
    Will only accept max size of a 96-well, e.g. A01 to H12

    Args:
    -----
    plate: a list of lists where plate[row][col] = [conditions], e.g. plate[0][0] = ['dsRed', '6F']
    '''
    row_letters = 'ABCDEFGH'
    well_colToLet = {i-1: '{:0>2d}'.format(i) for i in range(1,13)} # Pad single digits with 0 so col is 01 not 1
    plate_map = dict()

    # Check if plate is w/in limits of 96-well
    if len(plate) > 8 or len(plate[0]) > 12:
        raise IncorrectWellSpec('The largest a plate can be is a 96-well')

    #  For plate[row][col], if there is a specified list of conditions then add it to the mapping
    for row in range(len(plate)):
        for col in range(len(plate[0])):
            wellname = row_letters[row] + well_colToLet[col]
            if plate[row][col] != None:
                plate_map[wellname] =  plate[row][col]

    return plate_map

def toPlateMap(well_spec_list):
    '''
    Converts rectangle specification of wells to dictionary representation.

    Args:
    -----
    well_spec_list: A list of rectangular well specifications where order of list specifies the list order.
                    e.g. well_list = [{'A01-B12':'dsRed'}, {'A01-A12':'6F'}] will result in well 'A01':['dsRed', '6F']
                    Both 'A01' and  'A1' would be accepted in this case
                    A single well can also be specified, e.g. 'A01':'None'
    '''

    # initialize 96-well plate (max size we have)
    plate = [[None]*12 for i in range(8)] 

    # For each well spec (e.g. spec = {'A01-B12':'dsRed'})
    for (i, well_spec) in enumerate(well_spec_list):
        # For each well names (e.g. 'A01-B12')
        for (rect_well_names, cond) in well_spec.items():

            # Check if just a single well spec
            if re.search('\W', rect_well_names) == None:
                match = re.match('(?P<well1>\w{2,})', rect_well_names)
                coord1 = convWelltoCoord(match.group('well1'))
                row = coord1[0]
                col = coord1[1]
                if plate[row][col] == None:
                    plate[row][col] = [cond]
                else:
                    plate[row][col].append(cond)
                continue

            # Otherwise it's mult. wells:
            # Get coords for each well spect
            match = re.match('(?P<well1>\w{2,})\W(?P<well2>\w{2,})', rect_well_names)
            coord1 = convWelltoCoord(match.group('well1'))
            coord2 = convWelltoCoord(match.group('well2'))

            # Check if coords occur in right position
            if coord1[0] > coord2[0] or coord1[1] > coord2[1]:
                raise IncorrectWellSpec('Upper left wells must be specified first, e.g. \'A1-B12\' NOT \'B12-A1\'')

            # Add condition to appropriate wells
            for row in range(coord1[0], coord2[0]+1):
                for col in range(coord1[1], coord2[1]+1):
                    if plate[row][col] == None:
                        plate[row][col] = [cond] 
                    else:
                        plate[row][col].append(cond)

    # Convert plate to well dictionary mapping and return the dict map
    return convPlateToWellMap(plate)


"""
Helper module that parses plate specifications of the form:
MEF-low: A1-E1
MEF-bulk: F1-H1, A2-H2, A3-B3
retroviral: A1-H12
This format allows for robust and concise description of plate maps.
Specification
-------------
While these plate maps can be concisely defined inside YAML or JSON
files, this specification does not define an underlying format; it only
deals with how to handle the specification.
A *well specification* is a string containing a comma-separated list of
*region specifiers*. A region specifier is one of two forms, a single
well form:
    A1
    B05
or a rectangular region form:
    A1-A12
    B05-D8
    B05 - C02
As seen in these examples, the rectangular region form is distinguished
by the presence of a hyphen between two single-well identifiers. Whitespace
and leading zeros are allowed.
A well specification is first *normalized* by the software, where all whitespace
characters are removed. The resulting string is split by commas, and further parsed
as one of the region specifiers.
Within a single specifier, duplicate entries are *ignored*. That is, the following
specifiers are all equivilant:
    A5-B7
    A5,A6,A7,B5,B6,B7
    A5-B7,B6
    A5-B7,B5-B7
A *plate specification* is either a dictionary (if order is not important)
or a sequence of dictionaries (if order is important). The difference between these
in a YAML underlying format is:
test: A5-A7
test2: A5-A9
which yields {'test': 'A5-A7', 'test2': 'A5-A9'}
and
- test: A5-A7
- test2: A5-A9
which yields [{'test': 'A5-A7'}, {'test2': 'A5-A9'}]
This module reads either of these formats. It iterates over each of the well specifications,
building up a dictionary that maps wells to conditions. If multiple well specifications overlap,
then condition names are merged in the order in which they appear, separated by a separator
(by default, a period). This allows very concise condition layouts, such as the following:
conditions:
    MEF: A1-C12
    293: D1-F12
    untransformed: A1-D3
    experimental: A4-D12
will return a well map of the form:
{'A1': 'MEF.untransformed', ..., 'C10: 293.experimental'}
Returned well numbers are normalized (e.g. no leading zeros)
"""
def well_mapping(plate_spec, separator='.'):
    """
    Generates a well mapping, given a plate specification
    and an optional separator.
    Parameters
    ----------
    plate_spec: dict or iterable
        Either a single dictionary containing well specifications,
        or an iterable (list, tuple, etc) that returns dictionaries
        or well specifications as items.
    separator: str
        The separator to use for overlapping plate specifications
    
    Returns
    -------
    A dictionary that maps wells to conditions.
    """
    # Save plate_spec into a list of a single dictionary if it isn't already an iterable of dictionaries
    if isinstance(plate_spec, Mapping):
        plate_spec = [plate_spec]

    # Char To Int mapping and Int To Char mapping
    cti_mapping = {v: k for k, v in enumerate(list('ABCDEFGHIJKLMNOP'))}
    itc_mapping = {k: v for k, v in enumerate(list('ABCDEFGHIJKLMNOP'))}

    output_mapping = {}
    for mapping_dict in plate_spec:
        for key, val in mapping_dict.items():
            # Remove all whitespace
            tokenized = ''.join(val.split()).split(',')

            wells = set()
            for token in tokenized:
                single_result = re.fullmatch(r'^([A-P]\d+)$', token)
                dual_result = re.fullmatch(r'^([A-P]\d+)-([A-P]\d+)$', token)
                if single_result is None and dual_result is None:
                    raise ValueError(
                        'Invalid mapping spec: {}:{}, problem spec: {}'.format(key, val, token))

                if single_result is not None:
                    # Add a single well to the well mapping
                    wells.add('{}{:02d}'.format(
                        single_result.group(1)[0],
                        int(single_result.group(1)[1:])))
                else:
                    # Iterate over all wells
                    corners = [(cti_mapping[dual_result.group(i)[0]],
                                int(dual_result.group(i)[1:])) for i in range(1, 3)]
                    for well in itertools.product(
                            range(min(corners[0][0], corners[1][0]),
                                  max(corners[0][0], corners[1][0]) + 1),
                            range(min(corners[0][1], corners[1][1]),
                                  max(corners[0][1], corners[1][1]) + 1)):
                        wells.add('{}{:02d}'.format(
                            itc_mapping[well[0]], well[1]))
            for well in wells:
                if well not in output_mapping:
                    output_mapping[well] = key
                else:
                    output_mapping[well] = output_mapping[well] + \
                        separator + key
    return output_mapping


# Path
# user_path = Path.home() / 'OneDrive - Massachusetts Institute of Technology' / 'Documents - GallowayLab' / \
#     'instruments' / 'data' / 'keyence' / 'Nathan' / 'Reprogram'  

# root = '2021.08.16_NT_SlowFT_test_02'
# group_folder = '2021.08.16_NT_4dpi'

# # Actual path
# group_folder_path = user_path / root / group_folder

# # Read in 1st well map
# yaml_path = Path(group_folder_path)
# for f in yaml_path.glob('*yaml'):
#     with open(f) as file:
#         data = yaml.safe_load(file)
#         wellMap = well_mapping(data['wells'])
#     break

# reverse = True


# if reverse == False:
#     # Move files in group folder
#     moveFiles(Path(group_folder_path), wellMap, groupby=['cond'])
# else:
#     revMoveFiles(path=Path(group_folder_path))





parser = argparse.ArgumentParser(prog='kfm', description='Organize Keyence files')
parser.add_argument('group_folder_path', metavar='path', nargs='?', default='.',
                    help='Path to group folder. Default is current folder.')
group = parser.add_mutually_exclusive_group()
group.add_argument('-reverse', action='store_true',
                    help='Reverse kfm file move'
                    )
group.add_argument('-opt', dest='group_by', nargs='*', default=['natural'], choices=['none', 'XY', 'cond', 'T', 'stitch', 'Z', 'CH', 'natural'],
                    help='Grouping will be done in order, e.g. groupby=[\'XY\', \'Z\'] groups into group_folder_path/XY/Z. \
                          Natural grouping is done by condition/XY/stitch(opt)/Z(opt)/CH so you can easily scroll thru images.'
                    )
parser.add_argument('-ypath', dest='yaml_path', nargs='?',
                    help='Path to yaml file containing well description.'
                    )

args = parser.parse_args()

# If no yaml_path given, look in group folder path
if args.yaml_path == None:
    args.yaml_path = args.group_folder_path

# Read in 1st well map
yaml_path = Path(args.yaml_path)
for f in yaml_path.glob('*yaml'):
    with open(f) as file:
        data = yaml.safe_load(file)
        wellMap = well_mapping(data['wells'])
    break

if args.reverse == False:
    # Move files in group folder
    moveFiles(Path(args.group_folder_path), wellMap, groupby=args.group_by)
else:
    revMoveFiles(path=Path(args.group_folder_path))



import itertools
from collections.abc import Mapping
from pathlib import Path
import re
from datetime import datetime
import argparse
import yaml
import json
import sys
import shutil


class KfmError(RuntimeError):
    '''
    Rrror thrown for any runtime errors encountered when running kfm
    '''

class IncorrectWellSpec(KfmError):
    '''
    Runtime error thrown when well specification is out of order (e.g. 'A12-A03' or isn't an avail option e.g.'A1-A20')
    '''


class WellNotFound(KfmError):
    '''
    Runtime error thrown when well does not map to a Keyence XY# folder')
    '''


class IncorrectGroupbyError(KfmError):
    '''
    Runtime error thrown when groupby option isn't one of avail options ['none', 'XY', 'T', 'stitch', 'Z', 'CH'] or the option ['none'] is provided with other groupby args
    '''


class DestExistsError(KfmError):
    '''
    Runtime error thrown when trying to move a file to a destination that already contains a file with the same name
    '''


class RecordExistsError(KfmError):
    '''
    Runtime error thrown when trying to move when record still exists - should reverse move first before attempting more moves
    '''

class RecordDoesNotExistsError(KfmError):
    '''
    Runtime error thrown when trying to reverse move but record doesn't exists in the working directory
    '''


def match_img_type(path):
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

def map_XY_to_well(path):
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

def get_groupby_path(path, groupby, well_info, uniq_well_ID, match):
    '''
    Determine the path of where things will be moved depending on the groupby options
    '''

    # Create path depending on groupby options
    # groupby_opt = ['none', 'natural', 'XY', 'cond', 'T', 'stitch', 'Z', 'CH']

    # If none, don't specify any subdirectories b/c all will be dumped into the provided group_folder path
    if groupby[0] == 'none':
        return path

    # If natural grouping, then group by condition/XY so you can easily scroll thru images for a condition > in a well
    if groupby[0] == 'natural':
        groupby = ['cond', 'XY']

    # Then order in terms of what how the user specified
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


def check_groupby_opt(groupby, groupby_opt, img_type):
    '''
    Checks if the groupby options provided by user are valid. Raises IncorrectGroupbyError if incorrect.

    Args:
    -----
    groupby: A list of how to group images where order dictates order of subdirectories 
            (e.g. groupby=['XY', 'Z'] groups into group_folder_path/XY/Z).
    groupby_opt: The list of groupby options kfm can handle
    img_type: The image type given to kfm
    '''

    # Check if user provided groupby option is one of the groupby options that kfm can handle
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


def move_files(path, wellMap, groupby=['natural']):
    '''
    Main function that moves files. Default is grouping by 'natural' where all images get put in the natural ordering of: condition >> XY


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
    (img_type, pattern) = match_img_type(path)

    # Check if user provided groupby option is valid
    check_groupby_opt(groupby, groupby_opt, img_type)
    
    # Check if record.txt exists in the current group folder - if it has the whole move should be completely reversed before attempting new moves
    if (path/'record.txt').exists():
        raise RecordExistsError(
            'Files have already been moved. Reverse the move before trying to move files again.')
            

    # Create a record list to store where files were moved in format of (oldpath, newpath)
    record = list()
    # Create a directory list to store what files weren't moved
    unmoved_list = list()
    # Create a directory list to store what new directories were made
    new_dirs = list()

    # Deal with everything that's not a .tif by moving it into a 'unmoved' folder
    # note - don't need to do recursively b/c everything that's left behind in the group folder 
    #        will get moved at top subdirectory level
    unmoved_dest = path / 'unmoved'
    for f in path.glob('*'):
        # Skip if .DS_Store file in macs
        if f.name == '.DS_Store':
            continue
        unmoved_list.append((str(f), str(unmoved_dest/f.name)))
    new_dirs.append(str(unmoved_dest))
    

    # Map each XY to a well, e.g. XY01 is A01
    (XYtoWell, XYtoWell_unique) = map_XY_to_well(path)
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
        dest = get_groupby_path(path, groupby,
                              wellMap[well_ID], uniq_well_ID, match)

        # Add dest to list of directories to be made for the new groupby options if it's unique
        if not dest.exists() and dest not in new_dirs:
            new_dirs.append(str(dest))

        # Sub XY## in pic name with the well ID and info (e.g. A01(2)_6FDD)
        newFileName = re.sub(r'(XY\d+)', uniq_well_ID+'_'+wellMap[well_ID], f.name)
        dest = dest / newFileName

        # Record where file will be moved in order of (oldPath, newPath)
        record.append((str(f), str(dest)))

    # Check to see if dest exists for any files or directories that need to be moved (this shouldn't happen)
    for rec in record+unmoved_list:
        if Path(rec[1]).exists():
            raise(
                DestExistsError(
                    '\' {} \' could not be moved, destination already exists'.format(rec[1]))
            )

    # Record where files were moved in order of 1. unmoved files 2. tif files 3. any new directories made
    # This makes reversing moves easier b/c unmoved files include top level subdirectories that must be moved first
    # before any .tif files are moved (e.g. can't move .tif into path/XY01 if path/XY01 is now in path/misc/XY01)
    with open(path/'record.json', mode='w') as fid:

        json.dump({
            'record_time': datetime.now().strftime('%Y.%m.%d_%H.%M.%S'),
            'unmoved_list': unmoved_list,
            'record': record,
            'new_dirs': new_dirs}, fid)

    # Make all the new directories
    # [Path(new_dir).mkdir(parents=True) for new_dir in new_dirs]
    for new_dir in new_dirs:
        Path(new_dir).mkdir(parents=True)

    # Actually move files
    for rec in record+unmoved_list:
        src = Path(rec[0])
        dest = Path(rec[1])
        src.replace(dest)

    
     
def rev_move_files(path):
    '''
    Reverse the file move using history recorded in record.json

    Args:
    -----
    path: A path pointing to directory that has record.json which stores where files got moved to
    '''

    if not (path/'record.json').exists():
        raise RecordDoesNotExistsError('record.json not found in current working directory')
        
    new_dir_list = list()

    with open(path/'record.json', mode='r') as file:

        # Load json data for reversing the move
        rev_data = json.load(file)


        # For the unmoved and record files, check to see if dest exists before moving
        for rec in rev_data['unmoved_list']+rev_data['record']:
            if Path(rec[1]).exists():
                raise(
                    DestExistsError(
                        '\' {} \' could not be moved, destination already exists'.format(rec[1]))
                )

        # Actually reverse the move for unmoved and record
        for rec in rev_data['unmoved_list']+rev_data['record']:

            dest = Path(rec[0])
            src = Path(rec[1])
            src.replace(dest)
        
        # Delete any new directories that were made
        for newdir in rev_data['new_dirs']:
            shutil.rmtree(Path(newdir))

    # Print success msg
    print('Move successfully reversed at {}'.format(rev_data['record_time']))
    # Rename record.txt file
    (path/'record.json').rename(path/('{}_rev_{}'.format(rev_data['record_time'], 'record.json')))

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


'''
# Path
user_path = Path.home() / 'OneDrive - Massachusetts Institute of Technology' / 'Documents - GallowayLab' / \
    'instruments' / 'data' / 'keyence' / 'Nathan' / 'Reprogram'  

root = '2021.08.16_NT_SlowFT_test_02'
group_folder = '2021.08.16_NT_4dpi'

# Actual path
group_folder_path = user_path / root / group_folder



try:

    # Read in 1st well map
    yaml_path = Path(group_folder_path)

    for f in yaml_path.glob('*yaml'):
        with open(f) as file:
            data = yaml.safe_load(file)
            wellMap = well_mapping(data['wells'])
        break

    reverse = True

    if reverse == False:
        # Move files in group folder
        move_files(Path(group_folder_path), wellMap, groupby=['cond'])
    else:
        rev_move_files(path=Path(group_folder_path))

except KfmError as error:
    print('Error: ' + repr(error), file=sys.stderr)
    sys.exit(1)
'''



# Add arg parser
parser = argparse.ArgumentParser(prog='kfm', description='Organize Keyence files')

# Arg to specify group folder
parser.add_argument('group_folder_path', metavar='path', nargs='?', default='.',
                    help='Path to group folder. Default is current folder.')

# Arg to specify group by options or reverse the move
group = parser.add_mutually_exclusive_group()
group.add_argument('-rev', action='store_true',
                    help='Reverse kfm file move using the record.json file in group folder path'
                    )
group.add_argument('-opt', dest='group_by', nargs='*',
                    default=['cond'], choices=['none', 'XY', 'cond', 'T', 'stitch', 'Z', 'CH', 'natural'],
                    help='Grouping will be done in order, e.g. groupby=[\'XY\', \'Z\'] groups into group_folder_path/XY/Z. \
                          Natural grouping is done by condition/XY so you can easily scroll thru images. \
                          Default grouping is by condition.'
                    )

# Arg to specify path to yaml folder
parser.add_argument('-ypath', dest='yaml_path', nargs='?',
                    help='Path to yaml file containing well descriptions. Without, kfm will use the first yaml file it finds within the group folder.'
                    )

args = parser.parse_args()

try:
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

    if args.rev == False:
        # Move files in group folder
        move_files(Path(args.group_folder_path), wellMap, groupby=args.group_by)
    else:
        rev_move_files(path=Path(args.group_folder_path))

except KfmError as error:
    print('Error: ' + repr(error), file=sys.stderr)
    sys.exit(1)


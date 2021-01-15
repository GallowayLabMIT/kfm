import enum
from pathlib import Path
import re
import sys
from datetime import datetime


class IncorrectWellSpec(RuntimeError):
    '''
    Runtime error thrown when well specification is out of order (e.g. 'A12-A03' or isn't an avail option e.g.'A1-A20')
    '''


class IncorrectGroupbyError(RuntimeError):
    '''
    Runtime error thrown when groupby option isn't one of avail options ['none', 'XY', 'T', 'stitch', 'Z', 'CH'] or the option ['none'] is provided with other groupby args
    '''


class DestExistsError(RuntimeError):
    '''
    Runtime error thrown when trying to move a file to a destination that already contains a file with the same name
    '''


class recordExistsError(RuntimeError):
    '''
    Runtime error thrown when trying to move when record still exists - should reverse move first before attempting more moves
    '''

class recordDoesNotExistsError(RuntimeError):
    '''
    Runtime error thrown when trying to reverse move but record doesn't exists in the working directory
    '''

def matchImgType(path):
    """
    Given path to group folder, determine image type for the group folder
    """

    # Just check using first tif file found
    for f in path.rglob('*.tif'):
        isTimelapse = True if (re.search('_T(\d+)_', f.name) != None) else False
        isZstack = True if (re.search('_Z(\d+)_', f.name) != None) else False
        isStitch = True if (re.search('_(\d{5})_', f.name) != None) else False
        break
    
    img_type = {'isZstack': isZstack, 'isTimelapse': isTimelapse, 'isStitch': isStitch}

    # Make regex pattern where naming system is 'prefix_Timelapse_XY_Stitch_Zstack_Channel.tif'
    pattern = '(?P<prefix>\w+)'
    if img_type['isTimelapse']:
        pattern += '_T(?P<T>\d+)'
    pattern += '_XY(?P<XY>\d+)'
    if img_type['isStitch']:
        pattern += '_(?P<stitch>\d{5})'
    if img_type['isZstack']:
        pattern += '_Z(?P<Z>\d+)'
    pattern += '_(?P<CH>.*).tif'
    
    return (img_type, pattern)

def rm_tree(path, new_dirs):
    '''
    Recursively remove directories if it's not a newly made directory during the move
    '''
    for child in path.glob('*'):
        if child.is_dir() and path not in new_dirs:
            rm_tree(child)
    path.rmdir()

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
    for f in path.glob('*XY*/_*'):

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

def moveFiles(path, wellMap, groupby=['XY']):
    '''
    Move files. Default is grouping by 'XY'.

    Args:
    -----
    path: A path pointing to the group folder path (keyence naming system)
    wellMap: A dict mapping wells to conditions, e.g. {'A01': ['dsRed', 'None'], 'A02': ['dsRed', '6F']}
    groupby: A list of how to group images where order dictates order of subdirectories (e.g. groupby=['XY', 'Z'] groups into group_folder_path/XY/Z). Also whenever
    '''

    # All ways to group images
    groupby_opt = ['none', 'XY', 'T', 'stitch', 'Z', 'CH']

    # Check if user provided groupby option is correct and this is a new move (e.g. no record.txt exists)
    try:
        # Check if user provided groupby option is one of the avail options
        for group in groupby:
            if group not in groupby_opt:
                # print(b)
                raise(IncorrectGroupbyError(
                    'Cannot group by \'{}\', select from: {}'.format(group, groupby_opt)))
        
        # Check if user provided groupby is just none that it's the only option provided 
        if 'none' in groupby and len(groupby) != 1:
            raise(IncorrectGroupbyError(
                'If \'none\' option is selected, you cannot group by any other options as all images will be dumped into the group folder')
            )

        # Check if record.txt exists in the current group folder - if it has the whole move should be completely reversed before attempting new moves
        if (path/'record.txt').exists():
            raise recordExistsError(
                'Files have already been moved. Reverse the move before trying to move files again.')
            
    except RuntimeError as error:
        print('Error: ' + repr(error))
        return
    
    # Determine image type and patttern for regex matching
    (img_type, pattern) = matchImgType(path)

    # Map each XY to a well, e.g. XY01 is A01
    (XYtoWell, XYtoWell_unique) = mapXYtoWell(path)

    # Create a record list to store where files were moved in format of (oldpath, newpath)
    record = list()
    # Create a directory list to store what new directories were made
    new_dirs = list()

    for f in path.rglob('*'):

        # If not tif, move file to somewhere it won't bother anyone :)
        if f.name[-4:] != '.tif':  
            dest = path / 'unmoved'
        # Otherwise update the tif file name with well ID and info
        else: 
            # Extract metadata from img titles
            match = re.search(pattern, f.name)

            # Get well ID (e.g. A01) and well info (e.g. 6FDDRR)
            well_ID = XYtoWell['XY'+match.group('XY')]  # e.g. A01
            uniq_well_ID = XYtoWell_unique['XY'+match.group('XY')] # e.g. A01(2)
            well_info = '_'.join(wellMap[well_ID])  # e.g. if 'A01':['dsRed', '6F'] becomes dsRed_6F

            # Create path depending on groupby options
            dest = path
            for group_name in groupby:
                # If none, don't specify any subdirectories b/c all will be dumped into the provided group_folder path
                if group_name == 'none':
                    break
                # If XY replace with well info
                elif group_name == 'XY':
                    dest = dest / well_info
                else:
                    dest = dest / (group_name + match.group(group_name))

        # If dest dir doesn't exist, make one
        if not dest.exists():
            new_dirs.append(dest) # Note what new directories were made
            # Path(dest).mkdir(parents=True)

        # if tiff, make a new dest with the new file name
        if f.name[-4:] == '.tif': 
            # Sub XY## in pic name with the well ID and info (e.g. A01(2)_6FDD)
            newFileName = re.sub('(XY\d+)', uniq_well_ID+'_'+well_info, f.name)
            dest = dest / newFileName


        try:
            # If destination already exists, don't move it
            if dest.exists():
                raise(
                    DestExistsError(
                        '\' {} \' could not be moved, destination already exists'.format(dest))
                )
        except RuntimeError as error:
            print('Error: ' + repr(error))

        # Otherwise, move the file and record where it's been moved in order of (oldPath, newPath)
        # f.replace(dest)
        record.append((str(f), str(dest)))

    # Remove all the old directories
    # rm_tree(path, new_dirs)

    # Record where files got moved
    with open(path/'record.txt', mode='w') as fid:
        fid.write('Time of record: ' +
                datetime.now().strftime('%Y/%m/%d, %H:%M:%S') + '\n')
        for rec in record:
            fid.write(rec[0] + '\t' + rec[1] + '\n')
     
def revMoveFiles(path):
    '''
    Reverse the file move using history recorded in record.txt

    Args:
    -----
    path: A path pointing to directory that has record.txt which stores where files got moved to
    '''
    try:
        if not (path/'record.txt').exists():
            raise recordDoesNotExistsError('record.txt not found in current working directory')
            
        with open(path/'record.txt', mode='r') as fid:

            new_dirs = list()

            for i,f in enumerate(fid.readlines()):
                if i==0:
                    record_time = f
                else:
                    line = f.rstrip().split('\t')
                    src = line[0]
                    dest = line[1]

                    # If dest dir doesn't exist, make one
                    if not dest.exists():
                        new_dirs.append(dest)  # Note what new directories were made
                        Path(dest).mkdir(parents=True)

                    # If destination already exists, don't move it
                    if dest.exists():
                        raise(DestExistsError('\' {} \' could not be moved, destination already exists'.format(dest)))

        # Remove all the old directories
        rm_tree(path, new_dirs)

        # Success msg
        print('Move successfully reversed at {}'.format(record_time))

    except RuntimeError as error:
        print('Error: ' + repr(error))
        return

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
    '''

    # initialize 96-well plate (max size we have)
    plate = [[None]*12 for i in range(8)] 

    # For each well spec (e.g. spec = {'A01-B12':'dsRed'})
    for (i, well_spec) in enumerate(well_spec_list):
        # For each well names (e.g. 'A01-B12')
        for (rect_well_names, cond) in well_spec.items():

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





# well map
wellMap = {'A01': ['dsRed', 'None'], 'A02': ['dsRed', '6F']}

# Paths
user_path = Path.home() / 'OneDrive - Massachusetts Institute of Technology' / 'Documents - GallowayLab' / \
    'instruments' / 'data' / 'keyence' / 'Nathan'
root = 'test'
group_folder = 'testing_everything_copy'

# Actual path
group_folder_path = user_path / root / group_folder


# f = toPlateMap([{'A1-B12': 'dsRed'}, {'A01-D03': '6F'}])
# print('*'*20, '\n')
# print(f)
# convWelltoCoord('a1')
# rectWelltoArray('A01-B12', 'dsRed')
# rectWelltoArray('a01-B12', '6F')

# print('{:0>2d}'.format(12))
moveFiles(path=group_folder_path, wellMap=wellMap)
# moveFiles(path=group_folder_path, wellMap=wellMap, groupby=['M'])
# revMoveFiles(path)

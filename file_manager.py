import enum
from pathlib import Path
import re
import sys
from datetime import datetime


class IncorrectGroupbyError(RuntimeError):
    '''
    Runtime error thrown when groupby option isn't one of avail options ['XY', 'T', 'stitch', 'Z', 'CH']
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
    welltoXY = dict()
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
                XYtoWell_unique[welltoXY[well]] = well+'(1)'
                # Add dup. entry to unique mapping as (2) then change dup count to 2
                XYtoWell_unique[XY] = (well+'(2)')
                duplicates[well] = 2
            else:
                duplicates[well] += 1
                XYtoWell_unique[XY] = '{}({})'.format(well, duplicates[well])
        # Otherwise well is unique
        else:
            # Add XY mapping and add it as a unique well
            XYtoWell[XY] = well
            XYtoWell_unique[XY] = well
            welltoXY[well] = XY
            well_list.append(well)
    
    
    return (XYtoWell, XYtoWell_unique)

def moveFiles(path, wellMap, groupby=['XY']):
    '''
    Move files. Default is grouping by 'XY'
    '''

    # All ways to group images
    groupby_opt = ['XY', 'T', 'stitch', 'Z', 'CH']

    try:
        for group in groupby:
            if group not in groupby_opt:
                # print(b)
                raise(DestExistsError(
                    'Cannot group by \'{}\', select from: {}'.format(group, groupby_opt)))
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
            well_info = wellMap[well_ID]  # e.g. A01 is 6FDDRR

            # Create path depending on groupby options
            dest = path
            for group_name in groupby:

                # If XY replace with well info
                if group_name == 'XY':
                    dest = dest / well_info
                else:
                    dest = dest / (group_name + match.group(group_name))

        # If dest dir doesn't exist, make one
        if not dest.exists():
            new_dirs.append(dest) # Note what new directories were made
            Path(dest).mkdir(parents=True)

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
    rm_tree(path, new_dirs)

    # Record where files got moved
    try:
        if (path/'record.txt').exists():
            raise recordExistsError(
                'Files have already been moved. Reverse the move before trying to move files again.')
            
        with open(path/'record.txt', mode='w') as fid:
            fid.write('Time of record: ' +
                    datetime.now().strftime('%Y/%m/%d, %H:%M:%S') + '\n')
            for rec in record:
                fid.write(rec[0] + '\t' + rec[1] + '\n')

    except RuntimeError as error:
        print('Error: ' + repr(error))
        return
     
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


# well map
wellMap = {'A01': 'dsRed.None', 'A02': 'dsRed.6F'}

# Paths
user_path = Path.home() / 'OneDrive - Massachusetts Institute of Technology' / 'Documents - GallowayLab' / \
    'instruments' / 'data' / 'keyence' / 'Nathan'
root = 'test'
group_folder = 'testing_everything_Copy'

# Actual path
path = user_path / root / group_folder

# moveFiles(path=path, wellMap=wellMap)
# moveFiles(path=path, wellMap=wellMap, groupby=['M'])
# revMoveFiles(path)

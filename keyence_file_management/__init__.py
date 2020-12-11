#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 28 12:06:02 2020

@author: Nathan
"""

import shutil
import os
import csv
import re

def entrypoint():
    print("hello world")

    # source_dir = '/Users/Nathan/OneDrive\ -\ Massachusetts\ Institute\ of\ Technology/Documents\ -\ GallowayLab/instruments/data/keyence/Nathan/test/'

    # sp_source = '/2020.10.24.Hb9GFP.pPhage-SlowFT'
    # source_dir = source_dir + sp_source

    # # Map conditions to file names and wells
    # cond_name = dict()
    # well_name = dict()
    # with open(source_dir + '/key.csv', newline='', encoding='utf-8-sig') as csvfile:
    #     reader = csv.reader(csvfile, delimiter = ',')
    #     # row = ['XY##', 'WELL', 'CONDITION']
    #     for row in reader:
    #             cond_name[row[0]] = row[2]
    #             well_name[row[0]] = row[1]
                
    # # For each folder containing images (will start with XY)
    # folder_names = os.listdir(source_dir)
    # for folder in folder_names:
    #     if re.search('XY', folder):
            
    #         # Go thru each file and rename each channel/overlay image
    #         file_names = os.listdir(source_dir + '/' + folder)
    #         for file in file_names:
                
    #             CH_match = re.search('CH.', file)
    #             Overlay_match = re.search('Overlay', file)
    #             if CH_match:
    #                 new_file_name = (cond_name[folder] + '.' + well_name[folder] 
    #                     + '_' + CH_match.group(0)) + '.tif'
    #             elif Overlay_match:
    #                 new_file_name = (cond_name[folder] + '.' + well_name[folder] 
    #                     + '_' + Overlay_match.group(0)) + '.tif'
    #             else:
    #                 continue
            
    #             # Rename file and put in parent directory
    #             source = os.path.join(source_dir, folder, file)
    #             target = os.path.join(source_dir, new_file_name)
    #             shutil.copy2(source, target)

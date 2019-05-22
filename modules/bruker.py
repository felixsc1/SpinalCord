import re, os
import subprocess
import numpy as np

# def find_in_method(file):
#     with open(file) as f:
#         fulltext = f.read()
#         Search = re.compile('##\$Method=<(Bruker|User):(.+)>')
#         Search2 = re.compile('##\$PVM_ScanTimeStr=\\( 16 \\)\s<(.+)>')
#         Search3 = re.compile('##\$PVM_SPackArrSliceOrient=\\( 1 \\)\s(.+)')
#         result = Search.search(fulltext)
#         result2 = Search2.search(fulltext)
#         result3 = Search3.search(fulltext)
#         try:
#             result = result.group(2)
#         except:
#             result2 = 'unknown'
#         try:
#             result2 = result2.group(1)
#         except:
#             result2 = 'unknown' 
#         try:
#             result3 = result3.group(1)
#         except:
#             result3 = 'unknown'
#     return result, result2, result3


def find_in_method(file, string, selection=1):
    with open(file) as f:
        fulltext = f.read()
        Search = re.compile(string)
        result = Search.search(fulltext)
        try:
            result = result.group(selection)
        except:
            result = 'unknown'
    return result

def read_method_default(file):
    result1 = find_in_method(file, '##\$Method=<(Bruker|User):(.+)>', selection=2)
    result2 = find_in_method(file, '##\$PVM_ScanTimeStr=\\( 16 \\)\s<(.+)>')
    result3 = find_in_method(file, '##\$PVM_SPackArrSliceOrient=\\( 1 \\)\s(.+)')
    return result1, result2, result3

def get_sat_recovery_times(folder):
    file = os.path.join(folder, 'method')
    result = find_in_method(file, '##\$MultiRepTime=\\( \d+ \\)\s(.*)')
    if result == 'unknown':
        print('Warning! Could not find Saturation Reovery times. Is method file in folder? Is it a RAREVTR scan?')
    return np.array(result.split())



def convert_2dseq(folder_in, folder_out):
    """
    Requires Bru2 from github.
    Flags: 
    -a actual size (default is x10)
    -z compressed nii.gz
    """
    inputstring = f'Bru2 -a -z -o {folder_out} {folder_in}'
    subprocess.run(inputstring, shell=True, check=True)
    
    
    
def scantime_to_s(str_input):
    """
    takes as input a string in the form of __h__m__s__ms for scan duration as used in Bruker method files.
    Output is scantime in seconds. 
    """
    # expression only works for this time format: '0h1m12s679ms'
    regex = re.compile(r'(\d\d?)h(\d\d?)m(\d\d?)s(\d{,3})ms')
    result = regex.search(str_input)
    total_s = int(result.group(1)) * 3600 + int(result.group(2)) * 60 + int(result.group(3)) + int(result.group(4))/1000
    return total_s    

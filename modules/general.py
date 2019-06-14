import os, glob, fnmatch
import subprocess
from numpy import genfromtxt
import warnings


def runAFNI(inputstring, printout=True):
    if printout:
        print(inputstring)
    subprocess.run(inputstring,shell=True, check=True)
    
    
    
def extractROI(roifile, data, outfile):
    runAFNI(f'3dROIstats -mask {roifile} {data} > {outfile}', printout=False)
    print(f'ROI extracted to {outfile}')
    roidata = genfromtxt(outfile, delimiter='\t')
    warnings.simplefilter("ignore", RuntimeWarning)  #ignore the warning for line below (string values cant be evaluated)
    roi_numbers = roidata[roidata>0]
    return roi_numbers


def get_filepaths(mainpath, fileending='subject', subfolders=True):
    """
    Finds the files in ALL subfolders. (also used in other repos of mine)
    """
    filepaths = []
    
    if subfolders:
        for folderName, _subfolders, filenames in os.walk(mainpath):
            for file in filenames:
                if fnmatch.fnmatch(file, fileending):
                    filepaths.append(os.path.join(os.path.abspath(folderName),file))
    
    else:   
        filepaths = glob.glob(os.path.join(os.path.abspath(mainpath),fileending))

#     print('found: \n', filepaths)
            
  
    return filepaths
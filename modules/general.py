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
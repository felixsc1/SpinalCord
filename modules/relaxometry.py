import pandas as pd
import numpy as np

import matplotlib.pyplot as plt
import seaborn as sns
import scipy.stats as ss
import warnings  # for sns joinplot, its complaining

from collections import defaultdict


def getExcel(excelfile, header=0): 
    info = pd.read_excel(excelfile, convert_float=True, header=header)
    try:
        info.columns = map(str.lower, info.columns)
    except:
        pass
#         print('column titles should not start with numbers')
    return(info)  


def nested_dict(n, type):
    # see: https://stackoverflow.com/questions/29348345/declaring-a-multi-dimensional-dictionary-in-python
    if n == 1:
        return defaultdict(type)
    else:
        return defaultdict(lambda: nested_dict(n-1, type))



def cleanup_dimitri(df):
    
    df[df['rat id']==""] = np.NaN
    df['rat id'].fillna(method='ffill', inplace=True)   # fill empty rows that belong to same rat

    split = df['rat id'].str.split("_", expand=True)
    del df['rat id']
    df['group'] = split[0]
    df['date'] = split[1]
    df['id'] = split[2].astype(int)

#     split = df['id'].str.split("_", expand=True)  #some ids were in the form of:  212_1  212_2
#     df['id'] = split[0]
#     df['repetition'] = [1]
    
    
    split = df['acquisition/scan'].str.split(" ", expand=True)
    del df['acquisition/scan']
    df['acquisition'] = split[0]
    df['scan'] = split[1]

    df['group'].replace(regex=True,inplace=True,to_replace='.* ',value=r'')  # gives sham/sev/mod group (without the meanignless number)
    df.columns = [c.replace(' ', '_') for c in df.columns]  # prevent later errors due to spaces
    
    #some renames, to make plots etc nicer:
    rename_cols = {}
    rename_cols['unnamed:_18'] = 'comments' 
    rename_cols['cs_horizontal_mm'] = 'horizontal_cross_sec'
    rename_cols['cs_vertical'] = 'vertical_cross_sec'
    rename_cols['area_cm2_gm'] = 'GM_area_cm2'
    rename_cols['area_cm2_wm'] = 'WM_area_cm2'
    rename_cols['area_pu_gm'] = 'GM_voxel'
    rename_cols['area_pu_wm'] = 'WM_voxel'
    rename_cols['rm_wm'] = 'WM_mean'
    rename_cols['rm_gm'] = 'GM_mean'

    df.rename(columns=rename_cols, inplace=True)
    
#     df.replace({'nan',np.nan}, inplace=True)
    
    return df




def DTI_cleanup(DTI_raw):
    
    DTI_raw.iloc[:,1] = DTI_raw.iloc[:,1].astype(str) # assuming the scan infos are always in 2nd column

    info_rows = DTI_raw.iloc[:,1].str.contains('/.+/.+/')   # looking for something in form of scan/Sclice location/number/matter type   40/C6/139/GM

    import re

    # constructing a clean dataframe:
    DTI = pd.DataFrame()    
    split_info = pd.DataFrame()    
    for index, row in DTI_raw.iterrows():
        if info_rows[index]:
            date_id = re.search('_(20\d\d\d\d.*)_(\d\d\d)_', DTI_raw.iloc[index-1,1]) # this should be one row above the other infos, (regex: date is followed by _ and 3-digit animal ID)
            DTI.loc[index,'id'] = int(date_id.group(2))
            DTI.loc[index,'date'] = date_id.group(1)
            
            # continued: scan/Sclice location/number/matter type   40/C6/139/GM
            split_info = DTI_raw.iloc[index,1].split('/') 
            DTI.loc[index,'scan'] = split_info[0]
            DTI.loc[index,'segment'] = split_info[1]
            DTI.loc[index,'tissue'] = split_info[3]

            # now the values (warning lot of positional numbers hardcoded here)
            DTI.loc[index,'area'] = DTI_raw.iloc[index+1,2]
            DTI.loc[index,'AD'] = DTI_raw.iloc[index+1,3]
            DTI.loc[index,'FA'] = DTI_raw.iloc[index+2,3]
            DTI.loc[index,'MD'] = DTI_raw.iloc[index+3,3]
            DTI.loc[index,'RD'] = DTI_raw.iloc[index+4,3]
            DTI.loc[index,'comments'] = DTI_raw.iloc[index,8]
    return DTI







def insert_BBB_data(df, bbbfile):
	"""
	just to declutter notebook.
	very specific for this excel sheet. not really useful function for anything else...
	"""

	df_BBB = pd.read_excel(bbbfile)
	df_BBB.columns = [str(elem) for elem in df_BBB.columns] # because they were integers, which messes up indexing below

	df_BBB_selected = df_BBB[['AnimalNumber','1','84']]
	df_BBB_selected.rename(columns={'AnimalNumber':'id', '1':'BBB_day1', '84':'BBB_day84'}, inplace=True)
	df_BBB_selected.dropna(inplace=True)  
	df_BBB_selected['id'] = df_BBB_selected['id'].astype(int)

	df_BBB_selected.head()

	# df = pd.concat([df, df_BBB_selected], axis=1, sort=True)
	df = pd.merge(df, df_BBB_selected, on='id')   # see SQL terminology "on" is the key
	return df



def contrast_segment_selection_str(df, contrast, segment, columns):
	selected_rows = df[(df['location_estimate'] == segment) & (df['acquisition'] == contrast)]
	df_selection = selected_rows[columns]
	return df_selection


def contrast_segment_selection(df, selection, columns):
	selected_rows = df[(df['location_estimate'] == selection['segment']) & (df['acquisition'] == selection['contrast'])]
	df_selection = selected_rows[columns]
	return df_selection



def outlier_removal(df_selection, df, testcols, SD_cutoff=2, removerow=False):
	"""
	With removerow=True, complete row is removed if any of testcols is outlier.
	With removerow=False, all rows are kept, outliers just replaced by NaN (let plotting, stat functions deal with it hopefully...)
	"""
    
#     print('Any NaNs? ', df_selection.isnull().values.any())
	    # df_selection.info()
	    # print(df_selection.describe())
	    # df_selection.hist();

	# outlier removal:
	# all rows that are larger than x Standard Deviations (SD_cutoff) from mean in any of the tested columns are removed.

	if removerow:
		maskdf = pd.DataFrame()
		for c in testcols:
		    # df_selection shrinks with each iteration.
		    s = ((df_selection[c] - df_selection[c].mean()) / df_selection[c].std()).abs() < SD_cutoff
		    
		    df_selection = df_selection[s]
		    outlier_id = s[s == False]
#             print(f"removed outliers for column: {c} \n {df.loc[outlier_id.index, ['comments','id']]}")
	else:
		for c in testcols:
		    s = ((df_selection[c] - df_selection[c].mean()) / df_selection[c].std()).abs() < SD_cutoff

		    df_selection.loc[~s,c] = np.NaN
		    #df_selection[c] = np.NaN
		    outlier_id = s[s == False]
#             print(f"removed outliers for column: {c} \n {df.loc[outlier_id.index, ['comments','id']]}")
          
	#df_selection.hist();
	#plt.suptitle('Without outliers:', x=0.5, y=1.05, fontsize='large')
	return df_selection


## PLOTS ######
                  
                  
def jointplot_corr_DTI(df, segment='T6', tissue='GM', x='AD', y='BBB_day1'):
    """
    called with interact
    x and y are two column names within df.
    """
    warnings.filterwarnings("ignore")
    
    df_plot = df[(df['segment'] == segment) & (df['tissue'] == tissue)]
    try:
        g = sns.jointplot(x, y, data=df_plot, kind="reg", color="b", height=7,
#                     xlim=(np.round(0.9*df_plot[x].min()), np.round(1.1*df_plot[x].max())),
                       ylim=(np.round(0.8*df_plot[y].min()-1), np.round(1.2*df_plot[y].max())))
#                         .set_axis_labels("x", "y")) #add ( at beginning (sns...
        g.annotate(ss.pearsonr)
    except TypeError:
        print('column selection invalid')
                  
                  
def jointplot_corr(dfall, contrast, segment, x, y):
    """
    called with interact
    x and y are two columns within df.
    """
    warnings.filterwarnings("ignore")
    df = dfall[contrast][segment]
    try:
        g = sns.jointplot(x, y, data=df, kind="reg", color="b", height=7,
                       xlim=(np.round(0.95*df[x].min()-1), 1.05*df[x].max()+1),
                       ylim=(np.round(0.95*df[y].min()-1), 1.05*df[y].max()+1))
#                         .set_axis_labels("x", "y")) #add ( at beginning (sns...
        g.annotate(ss.pearsonr)
#     plt.show()

    except TypeError:
        print('column selection invalid')
        
        
        
def plot_boxplots_interactive(dfall, contrast, segment, columnI):
    df = dfall[contrast][segment]
    
    df.dropna(subset=[columnI], inplace=True)   #<--crucial for ANOVA!
    #why not dropping earlier? because now we look at only one column. For all others, the animal is still used.
    
    defpal = sns.color_palette("tab10")
    newPal = dict(sham = defpal[2], mild = defpal[0], mod = defpal[1], sev = defpal[3])
    
    plt.figure(figsize=(7,7))
    sns.boxplot(x="group", y=columnI, data=df, order=['sham', 'mild', 'mod', 'sev'], palette=newPal)
    sns.despine(trim=False, left=True)

    # ANOVA part:
    groupedData = df.groupby('group')[columnI].apply(list)
    groupedData.fillna(0, inplace=True)
    F, p = ss.f_oneway(*groupedData)
    print(f"ANOVA for {columnI}: F = {F}, p = {p}")
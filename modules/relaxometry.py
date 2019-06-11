import pandas as pd
import numpy as np


def getExcel(excelfile): 
    info = pd.read_excel(excelfile, convert_float=True)
    try:
        info.columns = map(str.lower, info.columns)
    except:
        print('column titles should not start with numbers')
    return(info)  


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
    return df


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






def contrast_segment_selection(df, selection, columns):
	selected_rows = df[(df['location_estimate'] == selection['segment']) & (df['acquisition'] == selection['contrast'])]
	df_selection = selected_rows[columns]
	return df_selection


def outlier_removal(df_selection, df, testcols, SD_cutoff=2, removerow=False):
	"""
	With removerow=True, complete row is removed if any of testcols is outlier.
	With removerow=False, all rows are kept, outliers just replaced by NaN (let plotting, stat functions deal with it hopefully...)
	"""

	print('Any NaNs? ', df_selection.isnull().values.any())
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
		    print(f"removed outliers for column: {c} \n {df.loc[outlier_id.index, ['comments','id']]}")
	else:
		for c in testcols:
		    s = ((df_selection[c] - df_selection[c].mean()) / df_selection[c].std()).abs() < SD_cutoff

		    df_selection.loc[~s,c] = np.NaN
		    #df_selection[c] = np.NaN
		    outlier_id = s[s == False]
		    print(f"removed outliers for column: {c} \n {df.loc[outlier_id.index, ['comments','id']]}")
          
	#df_selection.hist();
	#plt.suptitle('Without outliers:', x=0.5, y=1.05, fontsize='large')
	return df_selection



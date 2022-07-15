# General information for analyzer loading & statistics
# saving (to excel spreadsheet), displaying (to pyqt5)

import pandas
from pandas import DataFrame
from LazyLuna.loading_functions import *
from LazyLuna import Mini_LL
from PyQt5 import Qt, QtWidgets, QtGui, QtCore, uic
import traceback


########################################################################
########################################################################
## For conversion from Pandas DataFrame to PyQt5 Abstract Table Model ##
########################################################################
########################################################################

class DataFrameModel(QtGui.QStandardItemModel):
    def __init__(self, data, parent=None):
        QtGui.QStandardItemModel.__init__(self, parent)
        self._data = data
        for i in range(len(data.columns)):
            data_col = [QtGui.QStandardItem("{}".format(x)) for x in data.iloc[:,i].values]
            self.appendColumn(data_col)
        return

    def rowCount(self, parent=None):
        return len(self._data.values)

    def columnCount(self, parent=None):
        return self._data.columns.size

    def headerData(self, x, orientation, role):
        try:
            if orientation==QtCore.Qt.Horizontal and role==QtCore.Qt.DisplayRole:
                return self._data.columns[x]
            if orientation==QtCore.Qt.Vertical   and role==QtCore.Qt.DisplayRole:
                return self._data.index[x]
        except Exception as e:
            print('WARNING !!!: ', e)
        return None
    
    
########################
########################
## Custom Table Class ##
########################
########################
class Table:
    def __init__(self):
        self.df = DataFrame()
        
    # overwrite
    def calculate(self):
        self.df = DataFrame()
        
    def store(self, path):
        pandas.DataFrame.to_csv(self.df, path, sep=';', decimal=',')
        
    def to_pyqt5_table_model(self):
        return DataFrameModel(self.df)
        
        
# Present cases that can be compared to each other
class CC_OverviewTable(Table):
    def calculate(self, cases_df, reader_name1, reader_name2):
        reader1 = cases_df[cases_df['Reader']==reader_name1].copy()
        reader2 = cases_df[cases_df['Reader']==reader_name2].copy()
        #'SAX CINE', 'SAX CS', 'LAX CINE', 'SAX T1', 'SAX T2', 'SAX LGE'
        cc_df   = reader1.merge(reader2, how='inner', on=['Case Name', 'Age (Y)', 'Gender (M/F)', 'Weight (kg)', 'Height (m)',
                                                         'SAX CINE', 'SAX CS', 'LAX CINE', 'SAX T1', 'SAX T2', 'SAX LGE'])
        cc_df.rename({'Reader_x': 'Reader1', 'Reader_y': 'Reader2', 'Path_x': 'Path1', 'Path_y': 'Path2'}, inplace=True, axis=1)
        cc_df   = cc_df.reindex(columns=['Case Name', 'Reader1', 'Reader2', 'Age (Y)', 'Gender (M/F)', 'Weight (kg)', 'Height (m)', 'SAX CINE', 'SAX CS', 'LAX CINE', 'SAX T1', 'SAX T2', 'SAX LGE', 'Path1', 'Path2'])
        self.df = cc_df
    

class CC_ClinicalResultsTable(Table):
    def calculate(self, case_comparisons, with_dices=True, contour_names=['lv_endo','lv_myo','rv_endo']):
        rows = []
        case1, case2 = case_comparisons[0].case1, case_comparisons[0].case2
        columns=['case', 'reader1', 'reader2']
        for cr in case1.crs: columns += [cr.name+' '+case1.reader_name, cr.name+' '+case2.reader_name, cr.name+' difference']
        for cc in case_comparisons:
            c1, c2 = cc.case1, cc.case2
            try: # due to cases that couldn't be fitted
                row = [c1.case_name, c1.reader_name, c2.reader_name]
                for cr1, cr2 in zip(c1.crs, c2.crs):
                    row += [cr1.get_val(), cr2.get_val(), cr1.get_val_diff(cr2)]
                rows.append(row)
            except: rows.append([np.nan for _ in range(len(case1.crs)*3+3)])
        df = DataFrame(rows, columns=columns)
        if with_dices: df = pandas.concat([df, self.dices_dataframe(case_comparisons, contour_names)], axis=1, join="outer")
        self.df = df
        
    def dices_dataframe(self, case_comparisons, contour_names=['lv_endo','lv_myo','rv_endo']):
        rows = []
        columns = ['case', 'avg dice', 'avg dice cont by both', 'avg HD']
        for cc in case_comparisons:
            c1, c2 = cc.case1, cc.case2
            analyzer = Mini_LL.SAX_CINE_analyzer(cc)
            row = [c1.case_name]
            df = analyzer.get_case_contour_comparison_pandas_dataframe(fixed_phase_first_reader=False)
            all_dices = [d[1] for d in df[['contour name', 'DSC']].values if d[0] in contour_names]
            all_hds   = [d[1] for d in df[['contour name', 'HD' ]].values if d[0] in contour_names]
            row.append(np.mean(all_dices)); row.append(np.mean([d for d in all_dices if 0<d<100])); row.append(np.mean(all_hds))
            for cname in contour_names:
                dices = [d[1] for d in df[['contour name', 'DSC']].values if d[0]==cname]
                hds   = [d[1] for d in df[['contour name', 'HD' ]].values if d[0]==cname]
                row.append(np.mean(dices)); row.append(np.mean([d for d in dices if 0<d<100])); row.append(np.mean(hds))
            rows.append(row)
        for c in contour_names: columns.extend([c+' avg dice', c+' avg dice cont by both', c+' avg HD'])
        df = DataFrame(rows, columns=columns)
        return df
    
    def add_bland_altman_dataframe(self, case_comparisons):
        case1, case2 = case_comparisons[0].case1, case_comparisons[0].case2
        columns=[]
        for cr in case1.crs: columns += [cr.name+' '+case1.reader_name, cr.name+' '+case2.reader_name]
        for i in range(len(columns)//2):
            col_n = columns[i*2].replace(' '+case1.reader_name, ' avg').replace(' '+case2.reader_name, ' avg')
            self.df[col_n] = self.df[[columns[i*2], columns[i*2+1]]].mean(axis=1)
        

class CC_OverviewTable(Table):
    def calculate(self, cases_df, reader_name1, reader_name2):
        reader1 = cases_df[cases_df['Reader']==reader_name1].copy()
        reader2 = cases_df[cases_df['Reader']==reader_name2].copy()
        #'SAX CINE', 'SAX CS', 'LAX CINE', 'SAX T1', 'SAX T2', 'SAX LGE'
        cc_df   = reader1.merge(reader2, how='inner', on=['Case Name', 'Age (Y)', 'Gender (M/F)', 'Weight (kg)', 'Height (m)',
                                                         'SAX CINE', 'SAX CS', 'LAX CINE', 'SAX T1', 'SAX T2', 'SAX LGE'])
        cc_df.rename({'Reader_x': 'Reader1', 'Reader_y': 'Reader2', 'Path_x': 'Path1', 'Path_y': 'Path2'}, inplace=True, axis=1)
        cc_df   = cc_df.reindex(columns=['Case Name', 'Reader1', 'Reader2', 'Age (Y)', 'Gender (M/F)', 'Weight (kg)', 'Height (m)', 'SAX CINE', 'SAX CS', 'LAX CINE', 'SAX T1', 'SAX T2', 'SAX LGE', 'Path1', 'Path2'])
        self.df = cc_df

    
class CC_SAX_DiceTable(Table):
    def calculate(self, case_comparisons, contour_names=['lv_endo','lv_myo','rv_endo']):
        rows = []
        case1, case2 = case_comparisons[0].case1, case_comparisons[0].case2
        columns=['case name', 'cont by both', 'cont type', 'avg dice']
        for cc in case_comparisons:
            c1, c2 = cc.case1, cc.case2
            analyzer = Mini_LL.SAX_CINE_analyzer(cc)
            df = analyzer.get_case_contour_comparison_pandas_dataframe(fixed_phase_first_reader=False)
            all_dices = [d[1] for d in df[['contour name', 'DSC']].values if d[0] in contour_names]
            rows.append([c1.case_name, False, 'all', np.mean(all_dices)])
            rows.append([c1.case_name, True, 'all',  np.mean([d for d in all_dices if 0<d<100])])
            for cname in contour_names:
                dices = [d[1] for d in df[['contour name', 'DSC']].values if d[0]==cname]
                rows.append([c1.case_name, False, cname, np.mean(dices)])
                rows.append([c1.case_name, True, cname, np.mean([d for d in dices if 0<d<100])])
        self.df = DataFrame(rows, columns=columns)

        
class CC_ClinicalResultsAveragesTable(Table):
    def calculate(self, case_comparisons):
        rows = []
        case1, case2 = case_comparisons[0].case1, case_comparisons[0].case2
        columns=['Clinical Result', case1.reader_name, case2.reader_name, 'Diff('+case1.reader_name+', '+case2.reader_name+')']
        
        cr_dict1 = {cr.name+' '+cr.unit:[] for cr in case1.crs}
        cr_dict2 = {cr.name+' '+cr.unit:[] for cr in case1.crs}
        cr_dict3 = {cr.name+' '+cr.unit:[] for cr in case1.crs}
        for cc in case_comparisons:
            c1, c2 = cc.case1, cc.case2
            for cr1, cr2 in zip(c1.crs, c2.crs):
                cr_dict1[cr1.name+' '+cr1.unit].append(cr1.get_val())
                cr_dict2[cr1.name+' '+cr1.unit].append(cr2.get_val())
                cr_dict3[cr1.name+' '+cr1.unit].append(cr1.get_val_diff(cr2))
        rows = []
        for cr_name in cr_dict1.keys():
            row = [cr_name]
            row.append('{:.1f}'.format(np.nanmean(cr_dict1[cr_name])) + ' (' +
                      '{:.1f}'.format(np.nanstd(cr_dict1[cr_name])) + ')')
            row.append('{:.1f}'.format(np.nanmean(cr_dict2[cr_name])) + ' (' +
                      '{:.1f}'.format(np.nanstd(cr_dict2[cr_name])) + ')')
            row.append('{:.1f}'.format(np.nanmean(cr_dict3[cr_name])) + ' (' +
                      '{:.1f}'.format(np.nanstd(cr_dict3[cr_name])) + ')')
            rows.append(row)
        self.df = pandas.DataFrame(rows, columns=columns)
        

class CC_Metrics_Table(Table):
    def calculate(self, case_comparison, fixed_phase_first_reader=False):
        rows = []
        analyzer = Mini_LL.SAX_CINE_analyzer(case_comparison)
        self.metric_vals = analyzer.get_case_contour_comparison_pandas_dataframe(fixed_phase_first_reader)
        self.metric_vals = self.metric_vals[['category', 'slice', 'contour name', 'ml diff', 'abs ml diff', 'DSC', 'HD', 'has_contour1', 'has_contour2', 'position1', 'position2']]
        self.metric_vals.sort_values(by='slice', axis=0, ascending=True, inplace=True, ignore_index=True)
        
    def present_contour_df(self, contour_name, pretty=True):
        self.df = self.metric_vals[self.metric_vals['contour name']==contour_name]
        if pretty:
            self.df[['ml diff', 'abs ml diff', 'HD']] = self.df[['ml diff', 'abs ml diff', 'HD']].round(1)
            self.df[['DSC']] = self.df[['DSC']].astype(int)
        print(self.df)
        unique_cats = self.df['category'].unique()
        print('Unique categories; ', unique_cats)
        df = DataFrame()
        for cat_i, cat in enumerate(unique_cats):
            curr = self.df[self.df['category']==cat]
            curr = curr.rename(columns={k:cat+' '+k for k in curr.columns if k not in ['slice', 'category']})
            curr.reset_index(drop=True, inplace=True)
            if cat_i==0: df = curr
            else:        df = df.merge(curr, on='slice', how='outer')
        df = df.drop(labels=[c for c in df.columns if 'category' in c or 'contour name' in c], axis=1)
        df = self.resort(df, contour_name)
        self.df = df
        
    def resort(self, df, contour_name):
        metric_vals = self.metric_vals[self.metric_vals['contour name']==contour_name]
        unique_cats = metric_vals['category'].unique()
        n = len([c for c in df.columns if unique_cats[0] in c])
        cols = list(df.columns[0:1])
        for i in range(n): cols += [df.columns[1+i+j*n] for j in range(len(unique_cats))]
        return df[cols]

class LAX_CC_Metrics_Table(Table):
    def calculate(self, case_comparison, fixed_phase_first_reader=False):
        rows = []
        analyzer = Mini_LL.LAX_CINE_analyzer(case_comparison)
        self.metric_vals = analyzer.get_case_contour_comparison_pandas_dataframe(fixed_phase_first_reader)
        self.metric_vals = self.metric_vals[['category', 'slice', 'contour name', 'ml diff', 'abs ml diff', 'DSC', 'HD', 'has_contour1', 'has_contour2']]
        self.metric_vals.sort_values(by='slice', axis=0, ascending=True, inplace=True, ignore_index=True)
        #print('Here:/n', self.metric_vals)
        
    def present_contour_df(self, contour_name, pretty=True):
        self.df = self.metric_vals[self.metric_vals['contour name']==contour_name]
        if pretty:
            self.df[['ml diff', 'abs ml diff', 'HD']] = self.df[['ml diff', 'abs ml diff', 'HD']].round(1)
            self.df[['DSC']] = self.df[['DSC']].astype(int)
        unique_cats = self.df['category'].unique()
        df = DataFrame()
        for cat_i, cat in enumerate(unique_cats):
            #print(cat_i)
            curr = self.df[self.df['category']==cat]
            curr = curr.rename(columns={k:cat+' '+k for k in curr.columns if k not in ['slice', 'category']})
            curr.reset_index(drop=True, inplace=True)
            if cat_i==0: df = curr
            else:        df = df.merge(curr, on='slice', how='outer')
        df = df.drop(labels=[c for c in df.columns if 'category' in c or 'contour name' in c], axis=1)
        df = self.resort(df, contour_name)
        self.df = df
        
    def resort(self, df, contour_name):
        metric_vals = self.metric_vals[self.metric_vals['contour name']==contour_name]
        unique_cats = metric_vals['category'].unique()
        n = len([c for c in df.columns if unique_cats[0] in c])
        cols = list(df.columns[0:1])
        for i in range(n): cols += [df.columns[1+i+j*n] for j in range(len(unique_cats))]
        return df[cols]


class T1_CC_Metrics_Table(Table):
    def calculate(self, case_comparison, fixed_phase_first_reader=False):
        rows = []
        analyzer = Mini_LL.SAX_T1_analyzer(case_comparison)
        self.metric_vals = analyzer.get_case_contour_comparison_pandas_dataframe(fixed_phase_first_reader)
        self.metric_vals = self.metric_vals[['category', 'slice', 'contour name', 'DSC', 'HD', 'T1_R1', 'T1_R2', 'T1_Diff', 'Angle_Diff', 'has_contour1', 'has_contour2']]
        self.metric_vals.sort_values(by='slice', axis=0, ascending=True, inplace=True, ignore_index=True)
        
    def present_contour_df(self, contour_name, pretty=True):
        self.df = self.metric_vals[self.metric_vals['contour name']==contour_name]
        print(self.df)
        if pretty:
            self.df[['HD','T1_R1','T1_R2','T1_Diff']] = self.df[['HD','T1_R1','T1_R2','T1_Diff']].round(1)
            self.df[['Angle_Diff']] = self.df[['Angle_Diff']].round(1)
            self.df[['DSC']] = self.df[['DSC']].astype(int)
        print(self.df)
        unique_cats = self.df['category'].unique()
        print('Unique categories; ', unique_cats)
        df = DataFrame()
        for cat_i, cat in enumerate(unique_cats):
            curr = self.df[self.df['category']==cat]
            curr = curr.rename(columns={k:cat+' '+k for k in curr.columns if k not in ['slice', 'category']})
            curr.reset_index(drop=True, inplace=True)
            if cat_i==0: df = curr
            else:        df = df.merge(curr, on='slice', how='outer')
        df = df.drop(labels=[c for c in df.columns if 'category' in c or 'contour name' in c], axis=1)
        df = self.resort(df, contour_name)
        self.df = df
        
    def resort(self, df, contour_name):
        metric_vals = self.metric_vals[self.metric_vals['contour name']==contour_name]
        unique_cats = metric_vals['category'].unique()
        n = len([c for c in df.columns if unique_cats[0] in c])
        cols = list(df.columns[0:1])
        for i in range(n): cols += [df.columns[1+i+j*n] for j in range(len(unique_cats))]
        return df[cols]



class T2_CC_Metrics_Table(Table):
    def calculate(self, case_comparison, fixed_phase_first_reader=False):
        rows = []
        analyzer = Mini_LL.SAX_T2_analyzer(case_comparison)
        self.metric_vals = analyzer.get_case_contour_comparison_pandas_dataframe(fixed_phase_first_reader)
        self.metric_vals = self.metric_vals[['category', 'slice', 'contour name', 'DSC', 'HD', 'T2_R1', 'T2_R2', 'T2_Diff', 'Angle_Diff', 'has_contour1', 'has_contour2']]
        self.metric_vals.sort_values(by='slice', axis=0, ascending=True, inplace=True, ignore_index=True)
        
    def present_contour_df(self, contour_name, pretty=True):
        self.df = self.metric_vals[self.metric_vals['contour name']==contour_name]
        print(self.df)
        if pretty:
            self.df[['HD','T2_R1','T2_R2','T2_Diff']] = self.df[['HD','T2_R1','T2_R2','T2_Diff']].round(1)
            self.df[['Angle_Diff']] = self.df[['Angle_Diff']].round(1)
            self.df[['DSC']] = self.df[['DSC']].astype(int)
        print(self.df)
        unique_cats = self.df['category'].unique()
        print('Unique categories; ', unique_cats)
        df = DataFrame()
        for cat_i, cat in enumerate(unique_cats):
            curr = self.df[self.df['category']==cat]
            curr = curr.rename(columns={k:cat+' '+k for k in curr.columns if k not in ['slice', 'category']})
            curr.reset_index(drop=True, inplace=True)
            if cat_i==0: df = curr
            else:        df = df.merge(curr, on='slice', how='outer')
        df = df.drop(labels=[c for c in df.columns if 'category' in c or 'contour name' in c], axis=1)
        df = self.resort(df, contour_name)
        self.df = df
        
    def resort(self, df, contour_name):
        metric_vals = self.metric_vals[self.metric_vals['contour name']==contour_name]
        unique_cats = metric_vals['category'].unique()
        n = len([c for c in df.columns if unique_cats[0] in c])
        cols = list(df.columns[0:1])
        for i in range(n): cols += [df.columns[1+i+j*n] for j in range(len(unique_cats))]
        return df[cols]




        
class SAX_Cine_CCs_pretty_averageCRs_averageMetrics_Table(Table):
    def calculate(self, case_comparisons, view):
        cr_table = CC_ClinicalResultsTable()
        cr_table.calculate(case_comparisons, with_dices=True)
        means_cr_table = cr_table.df[['LVEF difference', 'LVEDV difference', 'LVESV difference', 'lv_endo avg dice', 
                             'lv_endo avg dice cont by both', 'lv_endo avg HD', 'LVM difference', 'lv_myo avg dice', 
                            'lv_myo avg dice cont by both', 'lv_myo avg HD', 'RVEF difference', 'RVEDV difference', 
                            'RVESV difference', 'rv_endo avg dice', 'rv_endo avg dice cont by both', 'rv_endo avg HD', 
                            'avg dice', 'avg dice cont by both', 'avg HD']].mean(axis=0)
        std_cr_table = cr_table.df[['LVEF difference', 'LVEDV difference', 'LVESV difference', 'lv_endo avg dice', 
                             'lv_endo avg dice cont by both', 'lv_endo avg HD', 'LVM difference', 'lv_myo avg dice', 
                            'lv_myo avg dice cont by both', 'lv_myo avg HD', 'RVEF difference', 'RVEDV difference', 
                            'RVESV difference', 'rv_endo avg dice', 'rv_endo avg dice cont by both', 'rv_endo avg HD', 
                            'avg dice', 'avg dice cont by both', 'avg HD']].std(axis=0)
        cr_table = pandas.concat([means_cr_table, std_cr_table], axis=1).reset_index()
        cr_table.columns = ['Name', 'Mean', 'Std']
        names = cr_table['Name']
        new_names = []
        for i, n in names.iteritems():
            n = n.replace(' difference', '').replace('avg HD','HD').replace('avg dice', 'Dice').replace('lv_endo', '').replace('rv_endo', '').replace('lv_myo','')
            if 'cont by both' in n: n = n.replace('cont by both', '(slices contoured by both)')
            elif 'Dice' in n:       n = n + ' (all slices)'
            if i>15:                     n = n + ' (all contours)'
            n = n.replace(') (', ', ')
            if 'HD' in n:                n = n + ' [mm]'
            if 'EF' in n or 'Dice' in n: n = n + ' [%]'
            if 'ESV' in n or 'EDV' in n: n = n + ' [ml]'
            if 'LVM' in n:               n = n + ' [g]'
            new_names.append(n)
        cr_table['Name'] = new_names
        self.cr_table = cr_table
        #display(cr_table)
        
        metrics_table = CCs_MetricsTable()
        metrics_table.calculate(case_comparisons, view)
        metrics_table = metrics_table.df
        
        rows = []
        for position in ['basal', 'midv', 'apical']:
            # Precision = tp / tp + fp
            # Recall    = tp / tp + fn
            # dice all slices
            # dice by both
            row1, row2 = [position, 'Dice (all slices) [%]'], [position, 'Dice (slices contoured by both) [%]']
            row3, row4 = [position, 'HD [mm]'], [position, 'Abs. ml diff. (per slice) [ml]']
            for contname in ['lv_endo', 'lv_myo', 'rv_endo']:
                print(position, contname)
                subtable = metrics_table[[k for k in metrics_table.columns if contname in k]]
                #display(subtable)
                dice_ks     = [k for k in subtable.columns if 'DSC' in k]
                position_ks = [k for k in subtable.columns if 'position1' in k]
                all_dices = []
                for ki in range(len(dice_ks)): all_dices.extend([d for d in subtable[subtable[position_ks[ki]]==position][dice_ks[ki]]])
                #print('all dices: ', all_dices)
                row1.append(np.mean(all_dices))
                row2.append(np.mean([d for d in all_dices if 0<d<100]))
                hd_ks = [k for k in subtable.columns if 'HD' in k]
                hds   = []
                for ki in range(len(hd_ks)): hds.extend([d for d in subtable[subtable[position_ks[ki]]==position][hd_ks[ki]]])
                #print('hds: ', hds)
                row3.append(np.mean(hds))
                # abs ml diff
                mld_ks = [k for k in subtable.columns if 'abs ml diff' in k]
                mlds   = []
                for ki in range(len(mld_ks)): mlds.extend([d for d in subtable[subtable[position_ks[ki]]==position][mld_ks[ki]]])
                #print('mlds: ', mlds)
                row4.append(np.mean(mlds))
            rows.extend([row1, row2, row3, row4])
        self.metrics_table = pandas.DataFrame(rows, columns=['Position', 'Metric', 'LV Endocardial Contour', 'LV Myocardial Contour', 'RV Endocardial Contour'])
        #display(self.metrics_table)
        
    def present_metrics(self):
        self.df = self.metrics_table
    
    def present_crs(self):
        self.df = self.cr_table
        
        
class CCs_MetricsTable(Table):
    def calculate(self, case_comparisons, view):
        cases = []
        for cc in case_comparisons:
            cc_table = CC_Metrics_Table()
            cc_table.calculate(cc)
            tables = []
            for c_i, contname in enumerate(view.contour_names):
                cc_table.present_contour_df(contname, pretty=False)
                cc_table.df = cc_table.df.rename(columns={k:contname+' '+k for k in cc_table.df.columns if 'slice' not in k})
                if c_i!=0: cc_table.df.drop(labels='slice', axis=1, inplace=True)
                tables.append(cc_table.df)
            table = pandas.concat(tables, axis=1)
            table['Case']    = cc.case1.case_name
            table['Reader1'] = cc.case1.reader_name
            table['Reader2'] = cc.case2.reader_name
            cols = list(table.columns)[-3:] + list(table.columns)[:-3]
            table = table[cols]
            cases.append(table)
        self.df = pandas.concat(cases, axis=0, ignore_index=True)
        

class T1_CCs_MetricsTable(Table):
    def calculate(self, case_comparisons, view):
        cases = []
        for cc in case_comparisons:
            cc_table = T1_CC_Metrics_Table()
            cc_table.calculate(cc)
            tables = []
            for c_i, contname in enumerate(view.contour_names):
                cc_table.present_contour_df(contname, pretty=False)
                cc_table.df = cc_table.df.rename(columns={k:contname+' '+k for k in cc_table.df.columns if 'slice' not in k})
                if c_i!=0: cc_table.df.drop(labels='slice', axis=1, inplace=True)
                tables.append(cc_table.df)
            table = pandas.concat(tables, axis=1)
            table['Case']    = cc.case1.case_name
            table['Reader1'] = cc.case1.reader_name
            table['Reader2'] = cc.case2.reader_name
            cols = list(table.columns)[-3:] + list(table.columns)[:-3]
            table = table[cols]
            cases.append(table)
        self.df = pandas.concat(cases, axis=0, ignore_index=True)
                

class T2_CCs_MetricsTable(Table):
    def calculate(self, case_comparisons, view):
        cases = []
        for cc in case_comparisons:
            cc_table = T2_CC_Metrics_Table()
            cc_table.calculate(cc)
            tables = []
            for c_i, contname in enumerate(view.contour_names):
                cc_table.present_contour_df(contname, pretty=False)
                cc_table.df = cc_table.df.rename(columns={k:contname+' '+k for k in cc_table.df.columns if 'slice' not in k})
                if c_i!=0: cc_table.df.drop(labels='slice', axis=1, inplace=True)
                tables.append(cc_table.df)
            table = pandas.concat(tables, axis=1)
            table['Case']    = cc.case1.case_name
            table['Reader1'] = cc.case1.reader_name
            table['Reader2'] = cc.case2.reader_name
            cols = list(table.columns)[-3:] + list(table.columns)[:-3]
            table = table[cols]
            cases.append(table)
        self.df = pandas.concat(cases, axis=0, ignore_index=True)
                

class CC_AngleAvgT1ValuesTable(Table):
    def calculate(self, case_comparison, category, nr_segments, byreader=None):
        self.cc = case_comparison
        r1, r2 = self.cc.case1.reader_name, self.cc.case2.reader_name
        self.category = category
        self.nr_segments, self.byreader = nr_segments, byreader
        cat1,  cat2  = self.cc.get_categories_by_example(category)
        
        rows    = []
        # prepare columns
        columns = ['Slice']
        testanno, testimg = cat1.get_anno(0,0), cat1.get_img (0,0, True, False)
        keys    = testanno.get_myo_mask_by_angles(testimg, nr_segments, None)
        for k in keys: 
            for r in [r1,r2,r1+'-'+r2]:
                columns += [r+' '+'('+'{:.1f}'.format(k[0])+'°, '+'{:.1f}'.format(k[1])+'°)']
        print(columns)
        
        for d in range(cat1.nr_slices):
            img1,  img2  = cat1.get_img (d,0, True, False), cat2.get_img (d,0, True, False)
            anno1, anno2 = cat1.get_anno(d,0), cat2.get_anno(d,0)
            refpoint = None
            if byreader is not None: refpoint = anno1.get_point('sacardialRefPoint') if byreader==1 else anno2.get_point('sacardialRefPoint')
            
            myo_vals1 = anno1.get_myo_mask_by_angles(img1, nr_segments, refpoint)
            myo_vals2 = anno2.get_myo_mask_by_angles(img2, nr_segments, refpoint)
            row = [d]
            for k in myo_vals1.keys():
                row += ['{:.1f}'.format(np.mean(myo_vals1[k]))]
                row += ['{:.1f}'.format(np.mean(myo_vals2[k]))]
                row += ['{:.1f}'.format(np.mean(myo_vals1[k])-np.mean(myo_vals2[k]))]
            
            rows.append(row)
        self.df = pandas.DataFrame(rows, columns=columns)
        
class LAX_CCs_MetricsTable(Table):
    def calculate(self, case_comparisons, view):
        cases = []
        for cc in case_comparisons:
            cc_table = LAX_CC_Metrics_Table()
            cc_table.calculate(cc)
            tables = []
            for c_i, contname in enumerate(view.contour_names):
                cc_table.present_contour_df(contname, pretty=False)
                cc_table.df = cc_table.df.rename(columns={k:contname+' '+k for k in cc_table.df.columns if 'slice' not in k})
                if c_i!=0: cc_table.df.drop(labels='slice', axis=1, inplace=True)
                tables.append(cc_table.df)
            table = pandas.concat(tables, axis=1)
            table['Case']    = cc.case1.case_name
            table['Reader1'] = cc.case1.reader_name
            table['Reader2'] = cc.case2.reader_name
            print('Columns: ', table.columns)
            cols = list(table.columns)[-3:] + list(table.columns)[:-3]
            table = table[cols]
            cases.append(table)
        self.df = pandas.concat(cases, axis=0, ignore_index=True)
        




class CC_StatsOverviewTable(Table):
    def get_dcm(self, cc):
        case = cc.case1
        for k in case.all_imgs_sop2filepath.keys():
            try: sop = next(iter(case.all_imgs_sop2filepath[k]))
            except: continue
            return pydicom.dcmread(case.all_imgs_sop2filepath[k][sop])
    def get_age(self, cc):
        try:
            age = self.get_dcm(cc).data_element('PatientAge').value
            age = float(age[:-1]) if age!='' else np.nan
        except: age=np.nan
        return age
    def get_gender(self, cc):
        try:
            gender = self.get_dcm(cc).data_element('PatientSex').value
            gender = gender if gender in ['M','F'] else np.nan
        except: gender=np.nan
        return gender
    def get_weight(self, cc):
        try:
            weight = self.get_dcm(cc).data_element('PatientWeight').value
            weight = float(weight) if weight is not None else np.nan
        except: weight=np.nan
        return weight
    def get_height(self, cc):
        try:
            h = self.get_dcm(cc).data_element('PatientSize').value
            h = np.nan if h is None else float(h)/100 if float(h)>3 else float(h)
        except: h=np.nan
        return h
    
    def calculate(self, ccs):
        columns = ['Nr Cases','Age (Y)','Gender (M/F)','Weight (kg)','Height (m)']
        ages    = np.array([self.get_age(cc) for cc in ccs])
        genders = [self.get_gender(cc) for cc in ccs]
        weights = np.array([self.get_weight(cc) for cc in ccs])
        heights = np.array([self.get_height(cc) for cc in ccs])
        
        rows = [[len(ccs), '{:.1f}'.format(np.mean(ages))+' ('+'{:.1f}'.format(np.std(ages))+')', 
                str(np.sum(genders=='M'))+'/'+str(np.sum(genders=='F')), 
                '{:.1f}'.format(np.mean(weights))+' ('+'{:.1f}'.format(np.std(weights))+')', 
                '{:.1f}'.format(np.mean(heights))+' ('+'{:.1f}'.format(np.std(heights))+')']]
        
        information_summary_df  = DataFrame(rows, columns=columns)
        self.df = information_summary_df
        
    
    
        
"""
def get_cases_table(cases, paths, debug=False):
    def get_dcm(case):
        for k in case.all_imgs_sop2filepath.keys():
            try: sop = next(iter(case.all_imgs_sop2filepath[k]))
            except: continue
            return pydicom.dcmread(case.all_imgs_sop2filepath[k][sop])
    def get_age(case):
        try:
            age = get_dcm(case).data_element('PatientAge').value
            age = float(age[:-1]) if age!='' else np.nan
        except: age=np.nan
        return age
    def get_gender(case):
        try:
            gender = get_dcm(case).data_element('PatientSex').value
            gender = gender if gender in ['M','F'] else np.nan
        except: gender=np.nan
        return gender
    def get_weight(case):
        try:
            weight = get_dcm(case).data_element('PatientWeight').value
            weight = float(weight) if weight is not None else np.nan
        except: weight=np.nan
        return weight
    def get_height(case):
        try:
            h = get_dcm(case).data_element('PatientSize').value
            h = np.nan if h is None else float(h)/100 if float(h)>3 else float(h)
        except: h=np.nan
        return h
    if debug: st = time()
    columns = ['Case Name', 'Reader', 'Age (Y)', 'Gender (M/F)', 'Weight (kg)', 'Height (m)', 'SAX CINE', 'SAX CS', 
               'LAX CINE', 'SAX T1', 'SAX T2', 'SAX LGE', 'Path']
    #print([c.available_types for c in cases])
    rows    = sorted([[c.case_name, c.reader_name, get_age(c), get_gender(c), get_weight(c), get_height(c), 
                       'SAX CINE' in c.available_types, 'SAX CS' in c.available_types, 'LAX CINE' in c.available_types, 
                       'SAX T1' in c.available_types, 'SAX T2' in c.available_types, 'SAX LGE' in c.available_types, paths[i]] 
                      for i, c in enumerate(cases)],
                     key=lambda p: str(p[0]))
    df      = pandas.DataFrame(rows, columns=columns)
    if debug: print('Took: ', time()-st)
    return df
"""
    
    
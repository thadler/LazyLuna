# General information for analyzer loading & statistics
# saving (to excel spreadsheet), displaying (to pyqt5)

import pandas
from pandas import DataFrame
from LazyLuna.loading_functions import *
from LazyLuna import Mini_LL
from PyQt5 import Qt, QtWidgets, QtGui, QtCore, uic


########################################################################
########################################################################
## For conversion from Pandas DataFrame to PyQt5 Abstract Table Model ##
########################################################################
########################################################################
class DataFrameModel(QtCore.QAbstractTableModel):
    DtypeRole = QtCore.Qt.UserRole + 1000
    ValueRole = QtCore.Qt.UserRole + 1001

    def __init__(self, df=pandas.DataFrame(), parent=None):
        super(DataFrameModel, self).__init__(parent)
        self._dataframe = df

    def setDataFrame(self, dataframe):
        self.beginResetModel()
        self._dataframe = dataframe.copy()
        self.endResetModel()

    def dataFrame(self):
        return self._dataframe

    dataFrame = QtCore.pyqtProperty(pandas.DataFrame, fget=dataFrame, fset=setDataFrame)

    @QtCore.pyqtSlot(int, QtCore.Qt.Orientation, result=str)
    def headerData(self, section:int, orientation:QtCore.Qt.Orientation, role:int=QtCore.Qt.DisplayRole):
        if role==QtCore.Qt.DisplayRole:
            if orientation==QtCore.Qt.Horizontal:
                return self._dataframe.columns[section]
            else: return str(self._dataframe.index[section])
        return QtCore.QVariant()

    def rowCount(self, parent=QtCore.QModelIndex()):
        if parent.isValid(): return 0
        return len(self._dataframe.index)

    def columnCount(self, parent=QtCore.QModelIndex()):
        if parent.isValid(): return 0
        return self._dataframe.columns.size

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < self.rowCount() \
            and 0 <= index.column() < self.columnCount()):
            return QtCore.QVariant()
        row = self._dataframe.index[index.row()]
        col = self._dataframe.columns[index.column()]
        dt  = self._dataframe[col].dtype
        val = self._dataframe.iloc[row][col]
        if role == QtCore.Qt.DisplayRole:      return str(val)
        elif role == DataFrameModel.ValueRole: return val
        if role == DataFrameModel.DtypeRole:   return dt
        return QtCore.QVariant()

    def roleNames(self):
        roles = {
            QtCore.Qt.DisplayRole:    b'display',
            DataFrameModel.DtypeRole: b'dtype',
            DataFrameModel.ValueRole: b'value'
        }
        return roles
    
    
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
    

class CC_StatsOverviewTable(Table):
    def calculate(self, cc_overview_table, restrict_to_view=None):
        cc_df = cc_overview_table.df
        if restrict_to_view is not None: 
            cc_df = cc_df[cc_df[restrict_to_view]]
        columns = ['Nr Cases','Age (Y)','Gender (M/F)','Weight (kg)','Height (m)']
        rows = [[len(cc_df.index), 
                 '{:.1f}'.format(cc_df['Age (Y)'].mean())+' ('+'{:.1f}'.format(cc_df['Age (Y)'].std())+')',
                 self.gender_string(cc_df),
                 '{:.1f}'.format(cc_df['Weight (kg)'].mean())+' ('+'{:.1f}'.format(cc_df['Weight (kg)'].std())+')',
                 '{:.1f}'.format(cc_df['Height (m)'].mean())+' ('+'{:.2f}'.format(cc_df['Height (m)'].std())+')']]
        information_summary_df  = DataFrame(rows, columns=columns)
        self.df = information_summary_df
        
    def gender_string(self, cc_df): # to resolve key errors when the cohort is only male or female
        counts     = cc_df['Gender (M/F)'].value_counts()
        nr_males   = counts['M'] if 'M' in counts.keys() else 0
        nr_females = counts['F'] if 'F' in counts.keys() else 0
        return str(nr_males)+'/'+str(nr_females)
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
                    row += [cr1.get_cr(), cr2.get_cr(), cr1.get_cr_diff(cr2)]
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
        
        cr_dict1 = {cr.name:[] for cr in case1.crs}
        cr_dict2 = {cr.name:[] for cr in case1.crs}
        cr_dict3 = {cr.name:[] for cr in case1.crs}
        for cc in case_comparisons:
            c1, c2 = cc.case1, cc.case2
            for cr1, cr2 in zip(c1.crs, c2.crs):
                cr_dict1[cr1.name].append(cr1.get_cr())
                cr_dict2[cr1.name].append(cr2.get_cr())
                cr_dict3[cr1.name].append(cr1.get_cr_diff(cr2))
        rows = []
        for cr_name in cr_dict1.keys():
            row = [cr_name]
            row.append('{:.1f}'.format(np.mean(cr_dict1[cr_name])))
            row.append('{:.1f}'.format(np.mean(cr_dict2[cr_name])))
            row.append('{:.1f}'.format(np.mean(cr_dict3[cr_name])))
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
        unique_cats = self.df['category'].unique()
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
                

    
    
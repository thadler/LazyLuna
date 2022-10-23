# General information for Analyzer Tool loading & statistics
# saving (to excel spreadsheet), displaying (to pyqt5)

import pandas
from pandas import DataFrame
from PyQt5 import Qt, QtWidgets, QtGui, QtCore, uic
import traceback

from LazyLuna.loading_functions import *
from LazyLuna.Metrics import *


########################################################################
## For conversion from Pandas DataFrame to PyQt5 Abstract Table Model ##
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
            if orientation==QtCore.Qt.Horizontal and role==QtCore.Qt.DisplayRole: return self._data.columns[x]
            if orientation==QtCore.Qt.Vertical   and role==QtCore.Qt.DisplayRole: return self._data.index[x]
        except Exception as e: print('WARNING in DataFrameModel!!!: ', traceback.format_exc())
        return None
    
    
########################
## Custom Table Class ##
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
            row = [c1.case_name]
            df = self.get_vals_for_dices(cc, contour_names)
            all_dices = [d[1] for d in df[['contour name', 'DSC']].values if d[0] in contour_names]
            all_hds   = [d[1] for d in df[['contour name', 'HD' ]].values if d[0] in contour_names]
            row.append(np.nanmean(all_dices)); row.append(np.nanmean([d for d in all_dices if 0<d<100])); row.append(np.nanmean(all_hds))
            for cname in contour_names:
                dices = [d[1] for d in df[['contour name', 'DSC']].values if d[0]==cname]
                hds   = [d[1] for d in df[['contour name', 'HD' ]].values if d[0]==cname]
                row.append(np.nanmean(dices)); row.append(np.nanmean([d for d in dices if 0<d<100])); row.append(np.nanmean(hds))
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
            
    def get_vals_for_dices(self, cc, contournames):
        from LazyLuna.Views import SAX_CINE_View
        dsc_m, hd_m = DiceMetric(), HausdorffMetric()
        view = SAX_CINE_View()
        case1, case2 = cc.case1, cc.case2
        rows, cols = [], ['casename', 'contour name', 'DSC', 'HD']
        for d in range(case1.categories[0].nr_slices):
            for cn in contournames:
                cats1, cats2 = view.get_categories(case1, cn), view.get_categories(case2, cn)
                for cat1, cat2 in zip(cats1, cats2):
                    try:
                        p1, p2 = cat1.phase, cat2.phase
                        dcm = cat1.get_dcm(d, p1)
                        anno1, anno2 = cat1.get_anno(d, p1), cat2.get_anno(d, p2)
                        cont1, cont2 = anno1.get_contour(cn), anno2.get_contour(cn)
                        dsc       = dsc_m.get_val(cont1, cont2, dcm, string=False)
                        hd        = hd_m .get_val(cont1, cont2, dcm, string=False)
                        rows.append([case1.case_name, cn, dsc, hd])
                    except: print(traceback.format_exc()); continue
        return DataFrame(rows, columns=cols)
        

class CC_OverviewTable(Table):
    def calculate(self, cases_df, reader_name1, reader_name2):
        reader1 = cases_df[cases_df['Reader']==reader_name1].copy()
        reader2 = cases_df[cases_df['Reader']==reader_name2].copy()
        #'SAX CINE', 'SAX CS', 'LAX CINE', 'SAX T1', 'SAX T2', 'SAX LGE'
        cc_df   = reader1.merge(reader2, how='inner', on=['Case Name', 'Age (Y)', 'Gender (M/F)', 'Weight (kg)', 'Height (m)',
                                                          'SAX CINE', 'SAX CS', 'LAX CINE', 'SAX T1 PRE', 'SAX T1 POST', 
                                                          'SAX T2', 'SAX LGE'])
        cc_df.rename({'Reader_x': 'Reader1', 'Reader_y': 'Reader2', 'Path_x': 'Path1', 'Path_y': 'Path2'}, inplace=True, axis=1)
        cc_df   = cc_df.reindex(columns=['Case Name', 'Reader1', 'Reader2', 'Age (Y)', 'Gender (M/F)', 'Weight (kg)', 'Height (m)', 'SAX CINE', 'SAX CS', 'LAX CINE', 'SAX T1 PRE', 'SAX T1 POST', 'SAX T2', 'SAX LGE', 'Path1', 'Path2'])
        self.df = cc_df
        
        

class CC_SAX_DiceTable(Table):
    def calculate(self, case_comparisons, contour_names=['lv_endo','lv_myo','rv_endo']):
        from LazyLuna.Views import SAX_CINE_View
        view = SAX_CINE_View()
        rows = []
        case1, case2 = case_comparisons[0].case1, case_comparisons[0].case2
        columns=['case name', 'cont by both', 'cont type', 'avg dice']
        for cc in case_comparisons:
            c1, c2 = cc.case1, cc.case2
            df = self.get_vals_for_dices(view, cc, contour_names)
            all_dices = [d[1] for d in df[['contour name', 'DSC']].values if d[0] in contour_names]
            rows.append([c1.case_name, False, 'all', np.nanmean(all_dices)])
            rows.append([c1.case_name, True, 'all',  np.nanmean([d for d in all_dices if 0<d<100])])
            for cname in contour_names:
                dices = [d[1] for d in df[['contour name', 'DSC']].values if d[0]==cname]
                rows.append([c1.case_name, False, cname, np.nanmean(dices)])
                rows.append([c1.case_name, True, cname, np.nanmean([d for d in dices if 0<d<100])])
        self.df = DataFrame(rows, columns=columns)
        
    
    def get_vals_for_dices(self, view, cc, contournames):
        dsc_m = DiceMetric()
        case1, case2 = cc.case1, cc.case2
        rows, cols = [], ['contour name', 'DSC']
        for d in range(case1.categories[0].nr_slices):
            for cn in contournames:
                cats1, cats2 = view.get_categories(case1, cn), view.get_categories(case2, cn)
                for cat1, cat2 in zip(cats1, cats2):
                    try:
                        p1, p2 = cat1.phase, cat2.phase
                        dcm = cat1.get_dcm(d, p1)
                        anno1, anno2 = cat1.get_anno(d, p1), cat2.get_anno(d, p2)
                        cont1, cont2 = anno1.get_contour(cn), anno2.get_contour(cn)
                        dsc       = dsc_m.get_val(cont1, cont2, dcm, string=False)
                        rows.append([cn, dsc])
                    except: print(traceback.format_exc()); continue
        return DataFrame(rows, columns=cols)
        


        
class CC_ClinicalResultsAveragesTable(Table):
    def calculate(self, case_comparisons):
        rows = []
        case1, case2 = case_comparisons[0].case1, case_comparisons[0].case2
        columns=['Clinical Result (mean±std)', case1.reader_name, case2.reader_name, 'Diff('+case1.reader_name+', '+case2.reader_name+')']
        
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
        
        metrics_table = SAX_CINE_CCs_Metrics_Table()
        metrics_table.calculate(view, case_comparisons, pretty=False)
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
                subtable = metrics_table[[k for k in metrics_table.columns if contname in k]]
                dice_ks     = [k for k in subtable.columns if 'DSC' in k]
                position_ks = [k for k in subtable.columns if 'Pos1' in k]
                all_dices = []
                for ki in range(len(dice_ks)): 
                    all_dices.extend([d for d in subtable[subtable[position_ks[ki]]==position][dice_ks[ki]]])
                row1.append(np.nanmean(all_dices))
                row2.append(np.nanmean([d for d in all_dices if 0<d<100]))
                hd_ks = [k for k in subtable.columns if 'HD' in k]
                hds   = []
                for ki in range(len(hd_ks)): hds.extend([d for d in subtable[subtable[position_ks[ki]]==position][hd_ks[ki]]])
                row3.append(np.nanmean(hds))
                # abs ml diff
                mld_ks = [k for k in subtable.columns if 'Abs ml Diff' in k]
                mlds   = []
                for ki in range(len(mld_ks)): mlds.extend([d for d in subtable[subtable[position_ks[ki]]==position][mld_ks[ki]]])
                row4.append(np.nanmean(mlds))
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
        

class CC_AngleAvgT1ValuesTable(Table):
    def calculate(self, case_comparison, category, nr_segments, byreader=None):
        self.cc = case_comparison
        r1, r2 = self.cc.case1.reader_name, self.cc.case2.reader_name
        self.category = category
        self.nr_segments, self.byreader = nr_segments, byreader
        cat1,  cat2  = self.cc.get_categories_by_example(category)
        
        rows, columns = [], ['Slice']
        testanno, testimg = cat1.get_anno(0,0), cat1.get_img (0,0, True, False)
        keys    = testanno.get_myo_mask_by_angles(testimg, nr_segments, None)
        for k in keys: 
            for r in [r1,r2,r1+'-'+r2]:
                columns += [r+' '+'('+'{:.1f}'.format(k[0])+'°, '+'{:.1f}'.format(k[1])+'°)']
        
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
        columns = ['Nr Cases','Age (Y)','Gender (M/F/Unknown)','Weight (kg)','Height (m)']
        ages    = np.array([self.get_age(cc) for cc in ccs])
        genders = np.array([self.get_gender(cc) for cc in ccs])
        weights = np.array([self.get_weight(cc) for cc in ccs])
        heights = np.array([self.get_height(cc) for cc in ccs])
        
        rows = [[len(ccs), '{:.1f}'.format(np.nanmean(ages))+' ('+'{:.1f}'.format(np.nanstd(ages))+')', 
                str(np.sum(genders=='M'))+'/'+str(np.sum(genders=='F'))+'/'+str(int(np.sum([1 for g in genders if g not in ['M','F']]))), 
                '{:.1f}'.format(np.nanmean(weights))+' ('+'{:.1f}'.format(np.nanstd(weights))+')', 
                '{:.1f}'.format(np.nanmean(heights))+' ('+'{:.1f}'.format(np.nanstd(heights))+')']]
        
        information_summary_df  = DataFrame(rows, columns=columns)
        self.df = information_summary_df
        



class LAX_CC_Metrics_Table(Table):
    def calculate(self, view, cc, contname, fixed_phase_first_reader=False, pretty=True):
        dsc_m, hd_m, areadiff_m = DiceMetric(), HausdorffMetric(), AreaDiffMetric()
        case1, case2 = cc.case1, cc.case2
        cats1, cats2 = view.get_categories(case1, contname), view.get_categories(case2, contname)
        cols, row = [], []
        for cat1, cat2 in zip(cats1, cats2):
            try:
                p1, p2 = (cat1.phase, cat2.phase) if not fixed_phase_first_reader else (cat1.phase, cat1.phase)
                dcm = cat1.get_dcm(0, p1)
                anno1, anno2 = cat1.get_anno(0, p1), cat2.get_anno(0, p2)
                cont1, cont2 = anno1.get_contour(contname), anno2.get_contour(contname)
                area_diff = areadiff_m.get_val(cont1, cont2, dcm, string=pretty)
                dsc       = dsc_m.get_val(cont1, cont2, dcm, string=pretty)
                hd        = hd_m.get_val(cont1, cont2, dcm, string=pretty)
                has_cont1, has_cont2 = anno1.has_contour(contname), anno2.has_contour(contname)
                row.extend([area_diff, dsc, hd, has_cont1, has_cont2])
            except Exception as e: row.extend([np.nan, np.nan, np.nan, np.nan, np.nan]); print(traceback.format_exc())
            cols.extend([cat1.name+' Area Diff', cat1.name+' DSC', cat1.name+' HD', cat1.name+' hascont1', cat1.name+' hascont2'])
        self.df = DataFrame([row], columns=cols)

        
class LAX_CCs_MetricsTable(Table):
    def calculate(self, view, ccs, fixed_phase_first_reader=False, pretty=True):
        dsc_m, hd_m, areadiff_m = DiceMetric(), HausdorffMetric(), AreaDiffMetric()
        rows, cols = [], ['Casename']
        for i, cc in enumerate(ccs):
            row = [cc.case1.case_name]
            case1, case2 = cc.case1, cc.case2
            for contname in view.contour_names:
                cats1, cats2 = view.get_categories(case1, contname), view.get_categories(case2, contname)
                for cat1, cat2 in zip(cats1, cats2):
                    try:
                        p1, p2 = (cat1.phase, cat2.phase) if not fixed_phase_first_reader else (cat1.phase, cat1.phase)
                        dcm = cat1.get_dcm(0, p1)
                        anno1, anno2 = cat1.get_anno(0, p1), cat2.get_anno(0, p2)
                        cont1, cont2 = anno1.get_contour(contname), anno2.get_contour(contname)
                        area_diff = areadiff_m.get_val(cont1, cont2, dcm, string=pretty)
                        dsc       = dsc_m.get_val(cont1, cont2, dcm, string=pretty)
                        hd        = hd_m.get_val(cont1, cont2, dcm, string=pretty)
                        has_cont1, has_cont2 = anno1.has_contour(contname), anno2.has_contour(contname)
                        row.extend([area_diff, dsc, hd, has_cont1, has_cont2])
                    except Exception as e: row.extend([np.nan, np.nan, np.nan, np.nan, np.nan]); print(traceback.format_exc())
                    if i==0: 
                        n, cn = cat1.name, contname
                        cols.extend([cn+' '+n+' Area Diff', cn+' '+n+' DSC', cn+' '+n+' HD', cn+' '+n+' hascont1', cn+' '+n+' hascont2'])
            rows.append(row)
        self.df = DataFrame(rows, columns=cols)
        
        

class T1_CC_Metrics_Table(Table):
    def get_column_names(self, cat):
        n = cat.name
        return [n+' Area Diff', n+' DSC', n+' HD', n+' T1avg_r1', n+' T1avg_r2', n+' T1avgDiff', n+' AngleDiff', n+' hascont1', cat1.name+' hascont2']
    
    def calculate(self, view, cc, contname, fixed_phase_first_reader=False, pretty=True):
        dsc_m, hd_m, areadiff_m = DiceMetric(), HausdorffMetric(), AreaDiffMetric()
        t1avg_m, t1avgdiff_m, angle_m = T1AvgReaderMetric(), T1AvgDiffMetric(), AngleDiffMetric()
        case1, case2 = cc.case1, cc.case2
        cats1, cats2 = view.get_categories(case1, contname), view.get_categories(case2, contname)
        rows, cols = [], []
        for cat1, cat2 in zip(cats1, cats2):
            for d in range(cat1.nr_slices):
                try:
                    dcm = cat1.get_dcm(d, 0)
                    img1 = cat1.get_img(d,0, True, False)
                    img2 = cat2.get_img(d,0, True, False)
                    anno1, anno2 = cat1.get_anno(d, 0), cat2.get_anno(d, 0)
                    cont1, cont2 = anno1.get_contour(contname), anno2.get_contour(contname)
                    area_diff = areadiff_m.get_val(cont1, cont2, dcm, string=pretty)
                    dsc       = dsc_m.get_val(cont1, cont2, dcm, string=pretty)
                    hd        = hd_m.get_val(cont1, cont2, dcm, string=pretty)
                    t1avg_r1, t1avg_r2 = t1avg_m.get_val(cont1, img1, string=pretty), t1avg_m.get_val(cont2, img2, string=pretty)
                    t1avg_diff = t1avgdiff_m.get_val(cont1, cont2, img1, img2, string=pretty)
                    angle_diff = angle_m.get_val(anno1, anno2, string=pretty)
                    has_cont1, has_cont2 = anno1.has_contour(contname), anno2.has_contour(contname)
                    rows.append([area_diff, dsc, hd, t1avg_r1, t1avg_r2, t1avg_diff, angle_diff, has_cont1, has_cont2])
                except Exception as e: rows.append([np.nan for _ in range(9)]); print(traceback.format_exc())
            cols = self.get_column_names(cat1)
        self.df = DataFrame(rows, columns=cols)
        
    

class T1_CCs_MetricsTable(Table):
    def get_column_names(self, cat):
        n = cat.name
        return ['Casename', 'Slice', n+' Area Diff', n+' DSC', n+' HD', n+' T1avg_r1', n+' T1avg_r2', n+' T1avgDiff', n+' Insertion Point AngleDiff', n+' hascont1', n+' hascont2']
    
    def calculate(self, view, ccs, fixed_phase_first_reader=False, pretty=True):
        dsc_m, hd_m, areadiff_m = DiceMetric(), HausdorffMetric(), AreaDiffMetric()
        t1avg_m, t1avgdiff_m, angle_m = T1AvgReaderMetric(), T1AvgDiffMetric(), AngleDiffMetric()
        rows, cols = [], []
        for i, cc in enumerate(ccs):
            case1, case2 = cc.case1, cc.case2
            contname = 'lv_myo'
            cats1, cats2 = view.get_categories(case1, contname), view.get_categories(case2, contname)
            for cat1, cat2 in zip(cats1, cats2):
                for d in range(cat1.nr_slices):
                    try:
                        dcm = cat1.get_dcm(d, 0)
                        img1 = cat1.get_img(d,0, True, False)
                        img2 = cat2.get_img(d,0, True, False)
                        anno1, anno2 = cat1.get_anno(d, 0), cat2.get_anno(d, 0)
                        cont1, cont2 = anno1.get_contour(contname), anno2.get_contour(contname)
                        area_diff = areadiff_m.get_val(cont1, cont2, dcm, string=pretty)
                        dsc       = dsc_m.get_val(cont1, cont2, dcm, string=pretty)
                        hd        = hd_m.get_val(cont1, cont2, dcm, string=pretty)
                        t1avg_r1, t1avg_r2 = t1avg_m.get_val(cont1, img1, string=pretty), t1avg_m.get_val(cont2, img2, string=pretty)
                        t1avg_diff = t1avgdiff_m.get_val(cont1, cont2, img1, img2, string=pretty)
                        angle_diff = angle_m.get_val(anno1, anno2, string=pretty)
                        has_cont1, has_cont2 = anno1.has_contour(contname), anno2.has_contour(contname)
                        rows.append([case1.case_name, d, area_diff, dsc, hd, t1avg_r1, t1avg_r2, t1avg_diff, angle_diff, has_cont1, has_cont2])
                    except Exception as e: rows.append([np.nan for _ in range(11)]); print(traceback.format_exc())
        cols = self.get_column_names(cat1)
        self.df = DataFrame(rows, columns=cols)
        
        
class T2_CC_Metrics_Table(T1_CC_Metrics_Table):
    def get_column_names(self, cat):
        n = cat.name
        return [n+' Area Diff', n+' DSC', n+' HD', n+' T2avg_r1', n+' T2avg_r2', n+' T2avgDiff', n+' AngleDiff', n+' hascont1', n+' hascont2']

class T2_CCs_MetricsTable(T1_CCs_MetricsTable):
    def get_column_names(self, cat):
        n = cat.name
        return ['Casename', 'Slice', n+' Area Diff', n+' DSC', n+' HD', n+' T2avg_r1', n+' T2avg_r2', n+' T2avgDiff', n+' Insertion Point AngleDiff', n+' hascont1', n+' hascont2']

    
class SAX_CINE_CC_Metrics_Table(Table):
    def get_column_names(self, view, case, contname):
        cols = []
        for cat in view.get_categories(case, contname): 
            n = cat.name
            cols.extend([n+' '+s for s in ['ml Diff', 'Area Diff', 'DSC', 'HD', 'Pos1', 'Pos2', 'hascont1', 'hascont2']])
        return cols
    
    def resort(self, row, cats):
        n = len(cats)
        n_metrics = len(row)//n
        ret = []
        for i in range(n_metrics):
            for j in range(n):
                ret.append(row[i+j*n_metrics])
        return ret
    
    def _is_apic_midv_basal_outside(self, case, d, p, cont_name):
        cat  = case.categories[0]
        anno = cat.get_anno(d, p)
        has_cont = anno.has_contour(cont_name)
        if not has_cont:                    return 'outside'
        if has_cont and d==0:               return 'basal'
        if has_cont and d==cat.nr_slices-1: return 'apical'
        prev_has_cont = cat.get_anno(d-1, p).has_contour(cont_name)
        next_has_cont = cat.get_anno(d+1, p).has_contour(cont_name)
        if prev_has_cont and next_has_cont: return 'midv'
        if prev_has_cont and not next_has_cont: return 'apical'
        if not prev_has_cont and next_has_cont: return 'basal'
    
    def calculate(self, view, cc, contname, fixed_phase_first_reader=False, pretty=True):
        mlDiff_m, dsc_m, hd_m, areadiff_m = mlDiffMetric(), DiceMetric(), HausdorffMetric(), AreaDiffMetric()
        case1, case2 = cc.case1, cc.case2
        cats1, cats2 = view.get_categories(case1, contname), view.get_categories(case2, contname)
        rows, cols = [], []
        for d in range(cats1[0].nr_slices):
            row = []
            for cat1, cat2 in zip(cats1, cats2):
                try:
                    p1, p2 = (cat1.phase, cat2.phase) if not fixed_phase_first_reader else (cat1.phase, cat1.phase)
                    dcm = cat1.get_dcm(d, p1)
                    anno1, anno2 = cat1.get_anno(d, p1), cat2.get_anno(d, p2)
                    cont1, cont2 = anno1.get_contour(contname), anno2.get_contour(contname)
                    ml_diff   = mlDiff_m.get_val(cont1, cont2, dcm, string=pretty)
                    area_diff = areadiff_m.get_val(cont1, cont2, dcm, string=pretty)
                    dsc       = dsc_m.get_val(cont1, cont2, dcm, string=pretty)
                    hd        = hd_m.get_val(cont1, cont2, dcm, string=pretty)
                    pos1 = self._is_apic_midv_basal_outside(case1, d, p1, contname)
                    pos2 = self._is_apic_midv_basal_outside(case2, d, p2, contname)
                    has_cont1, has_cont2 = anno1.has_contour(contname), anno2.has_contour(contname)
                    row.extend([ml_diff, area_diff, dsc, hd, pos1, pos2, has_cont1, has_cont2])
                except Exception as e: row.extend([np.nan for _ in range(8)]); print(traceback.format_exc())
            rows.append(self.resort(row, cats1))
        cols = self.resort(self.get_column_names(view, case1, contname), cats1)
        self.df = DataFrame(rows, columns=cols)
        
        

class SAX_CINE_CCs_Metrics_Table(Table):
    def get_column_names(self, view, case):
        cols = ['Casename', 'Slice']
        for cn in view.contour_names:
            cols_extension = []
            cats = view.get_categories(case, cn)
            for cat in cats:
                n = cat.name
                cols_extension.extend([cn+' '+n+' '+s for s in ['ml Diff', 'Abs ml Diff', 'Area Diff', 'DSC', 'HD', 'Pos1', 'Pos2', 'hascont1', 'hascont2']])
            cols.extend(self.resort(cols_extension, cats))
        return cols
    
    def resort(self, row, cats):
        n = len(cats)
        n_metrics = len(row)//n
        ret = []
        for i in range(n_metrics):
            for j in range(n):
                ret.append(row[i+j*n_metrics])
        return ret
    
    def _is_apic_midv_basal_outside(self, case, d, p, cont_name):
        cat  = case.categories[0]
        anno = cat.get_anno(d, p)
        has_cont = anno.has_contour(cont_name)
        if not has_cont:                    return 'outside'
        if has_cont and d==0:               return 'basal'
        if has_cont and d==cat.nr_slices-1: return 'apical'
        prev_has_cont = cat.get_anno(d-1, p).has_contour(cont_name)
        next_has_cont = cat.get_anno(d+1, p).has_contour(cont_name)
        if prev_has_cont and next_has_cont: return 'midv'
        if prev_has_cont and not next_has_cont: return 'apical'
        if not prev_has_cont and next_has_cont: return 'basal'
    
    def calculate(self, view, ccs, fixed_phase_first_reader=False, pretty=True):
        mlDiff_m, absmldiff_m, dsc_m, hd_m, areadiff_m = mlDiffMetric(), absMlDiffMetric(), DiceMetric(), HausdorffMetric(), AreaDiffMetric()
        rows, cols = [], []
        for cc in ccs:
            case1, case2 = cc.case1, cc.case2
            for d in range(case1.categories[0].nr_slices):
                row = [case1.case_name, d]
                for contname in view.contour_names:
                    cats1, cats2 = view.get_categories(case1, contname), view.get_categories(case2, contname)
                    row_extension = []
                    for cat1, cat2 in zip(cats1, cats2):
                        try:
                            p1, p2 = (cat1.phase, cat2.phase) if not fixed_phase_first_reader else (cat1.phase, cat1.phase)
                            dcm = cat1.get_dcm(d, p1)
                            anno1, anno2 = cat1.get_anno(d, p1), cat2.get_anno(d, p2)
                            cont1, cont2 = anno1.get_contour(contname), anno2.get_contour(contname)
                            ml_diff   = mlDiff_m.get_val(cont1, cont2, dcm, string=pretty)
                            absmldiff = absmldiff_m.get_val(cont1, cont2, dcm, string=pretty)
                            area_diff = areadiff_m.get_val(cont1, cont2, dcm, string=pretty)
                            dsc       = dsc_m.get_val(cont1, cont2, dcm, string=pretty)
                            hd        = hd_m.get_val(cont1, cont2, dcm, string=pretty)
                            pos1 = self._is_apic_midv_basal_outside(case1, d, p1, contname)
                            pos2 = self._is_apic_midv_basal_outside(case2, d, p2, contname)
                            has_cont1, has_cont2 = anno1.has_contour(contname), anno2.has_contour(contname)
                            row_extension.extend([ml_diff, absmldiff, area_diff, dsc, hd, pos1, pos2, has_cont1, has_cont2])
                        except Exception as e: row_extension.extend([np.nan for _ in range(9)]); print(traceback.format_exc())
                    row.extend(self.resort(row_extension, cats1))
                rows.append(row)
        cols = self.get_column_names(view, case1)
        self.df = DataFrame(rows, columns=cols)
    
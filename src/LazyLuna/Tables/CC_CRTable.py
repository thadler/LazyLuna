import pandas
from pandas import DataFrame
import traceback

from LazyLuna.Tables.Table import *
from LazyLuna.loading_functions import *
from LazyLuna.Metrics import *


class CCs_ClinicalResultsTable(Table):
    def calculate(self, case_comparisons, with_metrics=True, contour_names=['lv_endo','lv_myo','rv_endo']):
        """Presents table of Clinical Results for several Case_Comparisons (optionally with metric_values
        
        Args:
            case_comparisons (list of LazyLuna.Containers.Case_Comparison): list of case comparisons
            with_metrics (bool): if true, adds metric averages divided contour_names per case_comparison
            contour_names (list of str): the contour_names for which averages are added
        """
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
        if with_metrics: df = pandas.concat([df, self.metrics_dataframe(case_comparisons, contour_names)], axis=1, join="outer")
        self.df = df
    
    def metrics_dataframe(self, case_comparisons, contour_names=['lv_endo','lv_myo','rv_endo']):
        rows = []
        columns = ['case', 'avg dice', 'avg dice cont by both', 'avg HD']
        for cc in case_comparisons:
            c1, c2 = cc.case1, cc.case2
            row = [c1.case_name]
            df = self.get_metric_vals(cc, contour_names)
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
            
    def get_metric_vals(self, cc, contournames):
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
        
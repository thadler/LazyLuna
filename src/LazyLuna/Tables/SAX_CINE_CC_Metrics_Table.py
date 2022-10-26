import pandas
from pandas import DataFrame
import traceback

from LazyLuna.Tables.Table import *
from LazyLuna.loading_functions import *
from LazyLuna.Metrics import *



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
        """Presents table of Metric values for a Case_Comparison in SAX View
        
        Args:
            view (LazyLuna.Views.View): a view for the analysis
            cc (LazyLuna.Containers.Case_Comparison): contains two comparable cases
            contname (str): contour type to analyze
            fixed_phase_first_reader (bool): if True: forces phase for comparisons to the first reader's phase
            pretty (bool): if True casts metric values to strings with two decimal places
        """
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
        
        
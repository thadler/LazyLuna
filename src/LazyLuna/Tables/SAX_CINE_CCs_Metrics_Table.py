import pandas
from pandas import DataFrame
import traceback

from LazyLuna.Tables.Table import *
from LazyLuna.loading_functions import *
from LazyLuna.Metrics import *


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
        """Presents table of Metric values for all contour types of a list of Case_Comparisons
        
        Args:
            view (LazyLuna.Views.View): a view for the analysis
            ccs (list of LazyLuna.Containers.Case_Comparison): contains a list of case comparisons
            fixed_phase_first_reader (bool): if True: forces phase for comparisons to the first reader's phase
            pretty (bool): if True casts metric values to strings with two decimal places
        """
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
    
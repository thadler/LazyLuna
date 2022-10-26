import pandas
from pandas import DataFrame
import traceback

from LazyLuna.Tables.Table import *
from LazyLuna.loading_functions import *
from LazyLuna.Metrics import *


class T1_CCs_MetricsTable(Table):
    def get_column_names(self, cat):
        n = cat.name
        return ['Casename', 'Slice', n+' Area Diff', n+' DSC', n+' HD', n+' T1avg_r1', n+' T1avg_r2', n+' T1avgDiff', n+' Insertion Point AngleDiff', n+' hascont1', n+' hascont2']
    
    def calculate(self, view, ccs, fixed_phase_first_reader=False, pretty=True):
        """Presents Mapping specific metrics table for all contour types of a list of case comparisons
        
        Args:
            view (LazyLuna.Views.View): a view for the analysis
            case_comparisons (list of LazyLuna.Containers.Case_Comparison): list of case comparisons
            fixed_phase_first_reader (bool): if True: forces phase for comparisons to the first reader's phase
            pretty (bool): if True casts metric values to strings with two decimal places
        """
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
        
        
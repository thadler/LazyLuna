import pandas
from pandas import DataFrame
import traceback

from LazyLuna.Tables.Table import *
from LazyLuna.loading_functions import *
from LazyLuna.Metrics import *


class LAX_CC_Metrics_Table(Table):
    def calculate(self, view, cc, contname, fixed_phase_first_reader=False, pretty=True):
        """Presents table of Metric values for a Case_Comparison
        
        Args:
            view (LazyLuna.Views.View): a view for the analysis
            cc (LazyLuna.Containers.Case_Comparison): contains two comparable cases
            contname (str): contour type to analyze
            fixed_phase_first_reader (bool): if True: forces phase for comparisons to the first reader's phase
            pretty (bool): if True casts metric values to strings with two decimal places
        """
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

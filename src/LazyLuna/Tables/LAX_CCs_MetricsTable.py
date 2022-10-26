import pandas
from pandas import DataFrame
import traceback

from LazyLuna.Tables.Table import *
from LazyLuna.loading_functions import *
from LazyLuna.Metrics import *


        
class LAX_CCs_MetricsTable(Table):
    def calculate(self, view, ccs, fixed_phase_first_reader=False, pretty=True):
        """Presents table of Metric values for all contour types of a list of Case_Comparisons
        
        Args:
            view (LazyLuna.Views.View): a view for the analysis
            ccs (list of LazyLuna.Containers.Case_Comparison): list of case comparisons
            fixed_phase_first_reader (bool): if True: forces phase for comparisons to the first reader's phase
            pretty (bool): if True casts metric values to strings with two decimal places
        """
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
        
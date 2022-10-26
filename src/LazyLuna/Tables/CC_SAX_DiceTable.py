import pandas
from pandas import DataFrame
import traceback

from LazyLuna.Tables.Table import *
from LazyLuna.loading_functions import *
from LazyLuna.Metrics import *


class CC_SAX_DiceTable(Table):
    def calculate(self, case_comparisons, contour_names=['lv_endo','lv_myo','rv_endo']):
        """Calculates table with columns: case name, cont by both, cont type, avg dice
        
        Note:
            cont by both shows whether 1) all dice values are included (with slices not segmented by either reader (100%) and slices only segmented by one reader (0%) or 2) only dice values are included that were segmented by both readers
        
        Args:
            case_comparisons (list of LazyLuna.Containers.Case_Comparison): list of case comparisons
            contour_names (list of str): the contour_names for which averages are calculated
        """
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
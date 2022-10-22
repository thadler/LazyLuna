from time import time
import numpy as np
import pandas

from LazyLuna.Metrics import *
        

class SAX_CINE_analyzer:
    def __init__(self, case_comparison):
        self.cc   = case_comparison
        from LazyLuna.Views import SAX_CINE_View
        self.view = SAX_CINE_View()
        self.contour_comparison_pandas_dataframe = None

    def get_cat_depth_time2sop(self, fixed_phase_first_reader=False):
        cat_depth_time2sop = dict()
        categories = [self.cc.get_categories_by_example(c) for c in self.cc.case1.categories]
        for c1,c2 in categories:
            if np.isnan(c1.phase) or np.isnan(c2.phase): continue
            p1, p2 = (c1.phase, c2.phase) if not fixed_phase_first_reader else (c1.phase, c1.phase)
            for d in range(c1.nr_slices):
                sop1, sop2 = c1.depthandtime2sop[d,p1], c2.depthandtime2sop[d,p2]
                cat_depth_time2sop[(type(c1), d, p1, p2)] = (sop1, sop2)
        return cat_depth_time2sop

    def get_metric_values_depth_time(self, metric, cont_name, fixed_phase_first_reader=False, debug=False):
        if debug: st = time()
        metrics_dict = dict()
        cat_depth_time2sop = self.get_cat_depth_time2sop(fixed_phase_first_reader)
        for cat_type, d, p1, p2 in cat_depth_time2sop.keys():
            sop1, sop2 = cat_depth_time2sop[(cat_type, d, p1, p2)]
            cont1 = self.cc.case1.load_anno(sop1).get_contour(cont_name)
            cont2 = self.cc.case2.load_anno(sop2).get_contour(cont_name)
            dcm   = self.cc.case1.load_dcm(sop1)
            metrics_dict[(cat_type, d, p1, p2)] = metric.get_val(cont1, cont2, dcm)
        if debug: print('Calculating metrics by depth time took: ', time()-st)
        return metrics_dict

    def _is_apic_midv_basal_outside(self, d, p, cont_name, first_reader=True):
        case = self.cc.case1 if first_reader else self.cc.case2
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

    def get_case_contour_comparison_pandas_dataframe(self, fixed_phase_first_reader=False, debug=False):
        # case, reader1, reader2, sop1, sop2, category, d, nr_slices, depth_perc, p1, p2, cont_name, dsc, hd, mldiff, apic/midv/bas/outside1, apic/midv/bas/outside2, has_cont1, has_cont2
        if not self.contour_comparison_pandas_dataframe is None: return self.contour_comparison_pandas_dataframe
        if debug: st = time()
        rows                  = []
        view                  = self.view
        case1, case2          = self.cc.case1, self.cc.case2
        case_name             = case1.case_name
        reader1, reader2      = case1.reader_name, case2.reader_name
        dsc_m, hd_m, mldiff_m = DiceMetric(), HausdorffMetric(), mlDiffMetric()
        for cont_name in self.view.contour_names:
            categories1, categories2 = view.get_categories(case1, cont_name), view.get_categories(case2, cont_name)
            for cat1, cat2 in zip(categories1, categories2):
                if np.isnan(cat1.phase) or np.isnan(cat2.phase): continue
                p1, p2 = (cat1.phase, cat2.phase) if not fixed_phase_first_reader else (cat1.phase, cat1.phase)
                nr_sl  = cat1.nr_slices
                for d in range(cat1.nr_slices):
                    d_perc       = 1.0 * d / nr_sl
                    sop1, sop2   = cat1.depthandtime2sop[d,p1], cat2.depthandtime2sop[d,p2]
                    anno1, anno2 = self.cc.case1.load_anno(sop1), self.cc.case2.load_anno(sop2)
                    cont1, cont2 = anno1.get_contour(cont_name), anno2.get_contour(cont_name)
                    dcm    = self.cc.case1.load_dcm(sop1)
                    dsc    = dsc_m   .get_val(cont1, cont2, dcm)
                    hd     = hd_m    .get_val(cont1, cont2, dcm)
                    mldiff = mldiff_m.get_val(cont1, cont2, dcm)
                    has_cont1, has_cont2     = anno1.has_contour(cont_name), anno2.has_contour(cont_name)
                    apic_midv_basal_outside1 = self._is_apic_midv_basal_outside(d, p1, cont_name, first_reader=True)
                    apic_midv_basal_outside2 = self._is_apic_midv_basal_outside(d, p2, cont_name, first_reader=False)
                    row = [case_name, reader1, reader2, sop1, sop2, cat1.name, d, nr_sl, d_perc, p1, p2, cont_name, dsc, hd, mldiff, np.abs(mldiff), apic_midv_basal_outside1, apic_midv_basal_outside2, has_cont1, has_cont2]
                    rows.append(row)
        columns=['case', 'reader1', 'reader2', 'sop1', 'sop2', 'category', 'slice', 'max_slices', 'depth_perc', 'phase1', 'phase2', 'contour name', 'DSC', 'HD', 'ml diff', 'abs ml diff', 'position1', 'position2', 'has_contour1', 'has_contour2']
        df = pandas.DataFrame(rows, columns=columns)
        if debug: print('pandas table took: ', time()-st)
        return df

    
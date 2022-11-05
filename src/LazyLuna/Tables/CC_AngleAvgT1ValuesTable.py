import pandas
from pandas import DataFrame
import traceback

from LazyLuna.Tables.Table import *
from LazyLuna.loading_functions import *
from LazyLuna.Metrics import *


class CC_AngleAvgT1ValuesTable(Table):
    def calculate(self, case_comparison, category, nr_segments, byreader=None):
        """Takes one case_comparison customized by a mapping view and divides the myocardium by slices and segments
        
        Args:
            case_comparison (LazyLuna.Containers.Case_Comparison): two cases after View.customize_case(case)
            category (LazyLuna.Category): a mapping category for slice and contour access
            nr_segments (int): the number of myocardial segments
            byreader (None|1|2): (optional) if None then the insertion point is reader specific, otherwise it is taken from reader1 or reader 2.
        """
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
            if byreader is not None: refpoint = anno1.get_point('sax_ref') if byreader==1 else anno2.get_point('sax_ref')
            
            myo_vals1 = anno1.get_myo_mask_by_angles(img1, nr_segments, refpoint)
            myo_vals2 = anno2.get_myo_mask_by_angles(img2, nr_segments, refpoint)
            row = [d]
            for k in myo_vals1.keys():
                row += ['{:.1f}'.format(np.mean(myo_vals1[k]))]
                row += ['{:.1f}'.format(np.mean(myo_vals2[k]))]
                row += ['{:.1f}'.format(np.mean(myo_vals1[k])-np.mean(myo_vals2[k]))]
            
            rows.append(row)
        self.df = DataFrame(rows, columns=columns)
        
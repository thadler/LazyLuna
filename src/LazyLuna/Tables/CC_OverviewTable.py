import pandas
from pandas import DataFrame
import traceback

from LazyLuna.Tables.Table import *
from LazyLuna.loading_functions import *
from LazyLuna.Metrics import *


class CC_OverviewTable(Table):
    def calculate(self, cases_df, reader_name1, reader_name2):
        """Provides an overview of Cases refering to the same dicom datasets for two readers
        
        Note:
            cases_df has columns: [Case Name, Reader, Age (Y), Gender (M/F), Weight (kg), Height (m), SAX CINE, SAX CS, 
                                   LAX CINE, SAX T1 PRE, SAX T1 POST, SAX T2, SAX LGE]
        
        Args:
            cases_df (pandas.DataFrame): dataframe with information concerning cases
            reader_name1 (str): reader_name1
            reader_name2 (str): reader_name2
        """
        reader1 = cases_df[cases_df['Reader']==reader_name1].copy()
        reader2 = cases_df[cases_df['Reader']==reader_name2].copy()
        #'SAX CINE', 'SAX CS', 'LAX CINE', 'SAX T1', 'SAX T2', 'SAX LGE'
        cc_df   = reader1.merge(reader2, how='inner', on=['Case Name', 'Age (Y)', 'Gender (M/F)', 'Weight (kg)', 'Height (m)',
                                                          'SAX CINE', 'SAX CS', 'LAX CINE', 'SAX T1 PRE', 'SAX T1 POST', 
                                                          'SAX T2', 'SAX LGE'])
        cc_df.rename({'Reader_x': 'Reader1', 'Reader_y': 'Reader2', 'Path_x': 'Path1', 'Path_y': 'Path2'}, inplace=True, axis=1)
        cc_df   = cc_df.reindex(columns=['Case Name', 'Reader1', 'Reader2', 'Age (Y)', 'Gender (M/F)', 'Weight (kg)', 'Height (m)', 'SAX CINE', 'SAX CS', 'LAX CINE', 'SAX T1 PRE', 'SAX T1 POST', 'SAX T2', 'SAX LGE', 'Path1', 'Path2'])
        self.df = cc_df
        
        
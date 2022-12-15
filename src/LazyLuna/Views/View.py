from fpdf import FPDF
import os

class View:
    """View is a class that organizes cases.

    This includes:
        - Information on relevant contours
        - Assigning contours to categories and 
        - Connecting classes to the case when appropriate 

    Args:
        None

    Attributes:
        contour_names (list of str): List of strings referencing the contours
        contour2categorytype (dict of str: list of Category): Categories that reference the contour
    """
    
    def __init__(self):
        pass
    
    def initialize_case(self, case):
        """Takes a LazyLuna.Containers.Case object and tries to instantiate it according to this View
        
        Note:
            Initialize_case calculates relevant attributes (such as phases) for the case. This is a time-intensive operation (several seconds)
            
        Args:
            case (LazyLuna.Containers.Case object): The case to customize
            
        Returns:
            LazyLuna.Containers.Case: Returns input case with the view instantiated
        """
        pass
    
    def customize_case(self, case):
        """Takes a LazyLuna.Containers.Case object and attempts to reorganize it according to this View
        
        Note:
            Customize_case calculates relevant phases for the case. This is a fast operation
            
        Args:
            case (LazyLuna.Containers.Case object): The case to customize
            
        Returns:
            LazyLuna.Containers.Case: Returns input case with the view applied
        """
        pass

    def store_information(self, ccs, path, icon_path):
        """Takes a list of LazyLuna.Containers.Case_Comparison objects and stores relevant information
        
        Note:
            This function's execution time scales linearly with the number of cases and can be slow (several minutes)
            
        Args:
            case (list of LazyLuna.Containers.Case_Comparison): The case_comparisons to be analyzed
            path (str): Path to storage folder
        """
        pass
    
    


class PDF(FPDF):
    def prepare_pretty_format(self, icon_path=None):
        # Outside Rectangle
        self.set_fill_color(132.0, 132.0, 132.0) # color for outer rectangle
        self.rect(5.0, 5.0, 200.0, 287.0, 'DF')
        self.set_fill_color(255, 255, 255)       # color for inner rectangle
        self.rect(8.0, 8.0, 194.0, 281.0, 'FD')
        if not icon_path is None:
            try: 
                self.set_xy(170.0, 9.0)
                self.image(os.path.join(icon_path, 'HogwartsLineArt.png'),  link='', type='', w=2520/80, h=1920/80)
            except Exception as e: print('no icon path: ', e)
            try:
                self.set_xy(195.0, 7.5)
                self.image(os.path.join(icon_path, 'SlothLineArt.png'),  link='', type='', w=520/80, h=520/80)
            except Exception as e: print('no icon path: ', e)
            self.set_xy(173.5, 28.0)
            self.set_font('Times', 'B', 10)
            self.set_text_color(10, 10, 10)
            self.cell(w=25.0, h=6.0, align='C', txt='Lazy        Luna', border=0)
        
    def set_title(self, text):
        self.set_xy(0.0,0.0)
        self.set_font('Arial', 'B', 16)
        self.set_text_color(50, 50, 50)
        self.cell(w=210.0, h=40.0, align='C', txt=text, border=0)
        
    def set_text(self, text, x=10.0, y=80.0, font='Arial', size=8):
        self.set_xy(x, y)
        self.set_text_color(70.0, 70.0, 70.0)
        self.set_font(font, '', size)
        self.multi_cell(0, 5, text)
        
    def set_chart(self, plot_path, x=30.0, y=30, w=695/4, h=695/4):
        self.set_xy(x, y)
        self.image(plot_path, link='', type='', w=w, h=h)
        
        
    def set_table(self, data, spacing=1, fontsize=8, x=30.0, y=30, w=695/4, col_widths=None):
        self.set_xy(x, y)
        self.set_font('Arial', size=8)
        if col_widths is None: col_widths = [w/4.5 for i in range(len(data[0]))]
        else: pass
        row_height = fontsize
        for row in data:
            self.ln(row_height*spacing)
            curr_x = x
            for j, item in enumerate(row):
                self.set_x(curr_x)
                self.cell(col_widths[j], row_height*spacing, txt=item, border=1)
                curr_x += col_widths[j]

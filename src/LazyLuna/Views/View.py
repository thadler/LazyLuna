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
            Initialize_case calculates relevant phases for the case. This is a time-intensive operation (several seconds)
            
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

    def store_information(self, ccs, path):
        """Takes a list of LazyLuna.Containers.Case_Comparison objects and stores relevant information
        
        Note:
            This function's execution time scales linearly with the number of cases and can be slow (several minutes)
            
        Args:
            case (list of LazyLuna.Containers.Case_Comparison): The case_comparisons to be analyzed
            path (str): Path to storage folder
        """
        pass
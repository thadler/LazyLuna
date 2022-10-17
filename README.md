# LazyLuna
Lazy Luna is software for CMR analysis, which provides a backend for coders and a GUI tool for multilevel reader comparison.

## Description
Lazy Luna offers a number of base classes for multilevel reader comparison. Multilevel refers to comparisons on the image level (such as contour comparisons), on the patient level (such as differences between assessed clinical parameters) and the reader level (pertaining to statistical trends of reader differences).

#### Class Structure
Sequence or use-case specific classes can be inherited from these base classes in order to address specific or novel uses. The classes interact with each other in order to allow for these multilevel comparisons as described in the class diagram below. A detailed explanation can be found here: https://www.nature.com/articles/s41598-022-10464-w

<p align="center"> <img src="docs/Figure_classdiagram.png" width="700" title="Lazy Luna's Class Diagram!"> </p>

#### Graphical User Interface
Lazy Luna offers a GUI for reader and case comparison. This allows for loading selected cases from two readers, assessing their differences statistically and tracing them to contour origins.

<p align="center"> <img src="docs/Figure_tracing.png" width="700" title="Lazy Luna's Difference Tracing!"> </p>






## License and Use
MIT and please cite: https://www.nature.com/articles/s41598-022-10464-w
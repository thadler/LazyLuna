# LazyLuna
Lazy Luna is software for CMR analysis, which provides a backend for coders and a GUI tool for multilevel reader comparison.

## Description
Lazy Luna offers a number of base classes for multilevel reader comparison. Multilevel refers to comparisons on the image level (such as contour comparisons), on the patient level (such as differences between assessed clinical parameters) and the reader level (pertaining to statistical trends of reader differences).

Sequence or use-case specific classes can be inherited from these base classes in order to address specific or novel uses. The classes interact with each other in order to allow for these multilevel comparisons as described in the class diagram below. 

![Screenshot](docs/Figure_classdiagram.png)

<p align="center">
  <img src="docs/Figure_classdiagram.png" width="350" title="Hi there!">
</p>
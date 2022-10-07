---
title: 'InspectorCell: Finding Ground Truth in Multiplexed Microscopy Images'
tags:
  - Python
  - biology
  - multiplex
  - microscopy
  - annotation
authors:
  - name: Andre Gosselink
    orcid: 0000-0003-0181-456X
    equal-contrib: true
    affiliation: "1, 2"
  - name: Tatsiana Hofer
    equal-contrib: false
    affiliation: 3
  - name: Elvira Criado-Moronati
    equal-contrib: false
    affiliation: 2
  - name: Arndt von Haeseler
    equal-contrib: false
    affiliation: "3, 4"
  - name: Jutta Kollet
    equal-contrib: false
    affiliation: 2

affiliations:
  - name: Institute of Medical Statistics and Computational Biology, University of Cologne, Bachemer Str. 86, 50931 Cologne, Germany
    index: 1
  - name: R&D Department, Miltenyi Biotec B.V. & Co. KG, Friedrich Ebert Straße 68, 51429 Bergisch Gladbach, Germany
    index: 2
  - name: Center for Integrative Bioinformatics Vienna, Max Perutz Labs, University of Vienna, Medical University of Vienna, Dr. Bohr Gasse 9, 1030 Vienna, Austria
    index: 3
  - name: Faculty of Computer Science, University of Vienna, Währinger Str. 29, 1090 Vienna, Austria
    index: 4
date: 05 October 2022
bibliography: paper.bib

---

# Summary
Multiplexed immunofluorescence microscopy gives deep insights into multiple characteristics of cells in biological samples relevant to fields like cancer research. These characteristics are often image intensities that reflect the expression of a immunological markers on cell surfaces. Typical tasks in analyzing multiplexed microscopy images are the segmentation and quantification of these cell surfaces markers in a biological sample. Fore large datasets. these tasks are only feasible with automation, often using trained machine learning models.
However, the training of models for segmentation and quantification requires high-quality labeled training datasets. And recent increases in image stack sizes, the generation of labeled datasets for supervised machine learning has become a significant bottleneck. InspectorCell alleviates this bottleneck by providing an intuitive, graphical interface for synchronized manual segmentation and annotation of cells in highly multiplexed microscopy images. The modular implementation of InspectorCell in Python enables tight integration into existing applications such as Orange3 or CellProfiler. An image dataset with exemplary annotations is available at: https://doi.org/10.7303/syn37910913.2


# Statement of Need
The cellular composition of tumors is of great scientific interest as the presence of tumor-infiltrating lymphocytes correlates with the survival of cancer patients [@Idos2020; @Santoiemma2015]. Multiplexed tissue imaging methods like CODEX [@Goltsev2018] or MACSima™ [@Kinkhabwala2022] are used to investigate tumor samples' cellular characteristics. These techniques generate large image stacks of the same tumor sample slice, where each image covers the intensity profile of a specific cell surface marker. All cells in a tissue sample slice are categorized – for example, into cancer and immune cells – based on the cell surface marker intensities on each cell. This cell-based analysis for ever-growing large datasets seems to be only feasible with machine learning. However, a significant bottleneck when working with machine learning models is the lack of suitable multiplexed image datasets with segmented and quantified cells for model training.

Generating these datasets is time-consuming and cumbersome because current software does not integrate synchronized viewing, editing, and annotation of multiple images simultaneously. While it is possible to edit cell segments in CellProfiler [@Carpenter2006], only a single channel can be evaluated at a time. FIJI [@Schindelin2012] displays several immune images in parallel, but the different views on the images are not synchronized. An annotation or change of a cell segment must be performed in each window individually, but finding the exact location of a single cell in all images is cumbersome. Applications like ilastik [@Sommer2011] or CellPose [@Stringer2021]  fuse the analysis of images with the training of a machine learning model. However, a user can evaluate only one image at a time, and the generated data is not viable for subsequent model training.

We used InspectorCell to manually analyze cells in multiplexed immunofluorescence microscopy images of an ovarian cancer tissue slice obtained with the MACSima™ imaging platform. The tissue was stained with 99 cell markers, and a subset of the dataset is freely available[^1]. An initial cell segmentation was generated with CellProfiler and imported into InspectorCell. The cell segmentations were refined, and the cell marker expressions were quantified (fig. \autoref{fig:featandflow}a). In the initial CellProfiler segments were 1960 cells, and after refinement with InspectorCell, only 1750 cells remained. Among the immunological analysis results, we obtained a ground truth training dataset for subsequent model training, e.g., for continuous training of the CellPose model.

A synchronized overview over multiple images with editing capabilities for single-cell segmentation and quantification made this manual analysis possible. With InspectorCell, we provide a solution for efficient manual segmentation and annotation of large image stacks. The primary benefit of InspectorCell is the ability to view cells within the context of multiple cell markers, which accelerates manual analysis of cells in large image stacks. Expert immunologists can use InspectorCell to evaluate various cell characteristics at a glance and simultaneously generate high-quality training data.

[^1]: https://doi.org/10.7303/syn37910913.2


# Figures

![Exemplary use cases of InspectorCell. Segmentation of image stacks are opened with InspectorCell. (a) Six immunofluorescence images of the image stack are displayed side- by-side in a 3×2 grid. Cell segments are displayed as blue polygons (top). A synchronized multi cursor (orange) is a visual anchor in all channels. The CD3 channel (lower middle) is enlarged below the main window. The cell segment annotation is editable and displayed for the active cell segment in green font. (b) Over-segmentation can be merged with a single keystroke after mouse selection. (c) A cell segment (light blue) can be edited to embrace the marker signal area attributable to a distinct cell. Multiple segments can enclose the same areas to reflect cell overlaps and interactions. The manual edits of cell segmentations and annotations are saved in a single JSON file. Additionally, the JSON file can store extracted cell features, for example, mean pixel intensities.
\label{fig:featandflow}](doc/fig/featandflowS.png){ width=80% }

# Acknowledgements

We thank Ali Kinkhabwala for his help during development, Bianca Heemskerk for releasing the data, Paurush Praveen, Werner Müller and Achim Tresch for reviewing the manuscript.
This project was partially funded by Miltenyi Biotec B.V. & Co. KG.

# References

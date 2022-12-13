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
    affiliation: "1, 2"
  - name: Tatsiana Hofer
    affiliation: 3
  - name: Elvira Criado-Moronati
    affiliation: 2
  - name: Arndt von Haeseler
    affiliation: "3, 4"
  - name: Jutta Kollet
    affiliation: 2

affiliations:
  - name: Institute of Medical Statistics and Computational Biology, Faculty of Medicine, University of Cologne, Cologne, Germany
    index: 1
  - name: R&D Department, Miltenyi Biotec B.V. & Co. KG, Bergisch Gladbach, Germany
    index: 2
  - name: Center for Integrative Bioinformatics Vienna, Max Perutz Labs, University of Vienna, Medical University of Vienna, Vienna, Austria
    index: 3
  - name: Faculty of Computer Science, University of Vienna, Vienna, Austria
    index: 4
date: 05 October 2022
bibliography: paper.bib
---

# Summary
Multiplexed immunofluorescence microscopy gives deep insights into biological samples, like cancer tissues. The image intensities reflect the expression of immunological markers on the surfaces of cells that make up the tissue. Typical tasks in analyzing such images are segmenting cells and quantifying their cell surface markers. Novel microscopy methods generate large datasets with hundreds of images per biological sample. The analysis of such large datasets can only be performed using automation, nowadays by machine learning.
However, training models for segmentation and quantification require high-quality labeled datasets. Moreover, with recent increases in image stack sizes, the generation of labeled datasets for machine learning has become a significant bottleneck. InspectorCell alleviates this bottleneck by providing an intuitive, graphical interface for synchronized manual segmentation and annotation of cells in highly multiplexed microscopy images. The modular implementation of InspectorCell in Python enables tight integration into existing applications such as Orange3 or CellProfiler. An image dataset with exemplary annotations is available at: [https://doi.org/10.7303/syn37910913.2](https://doi.org/10.7303/syn37910913.2)

# Statement of Need
The cellular composition of tumors is of great scientific interest as the presence of tumor-infiltrating lymphocytes correlates with the survival of cancer patients [@Idos2020; @Santoiemma2015]. Multiplexed tissue imaging methods like CODEX [@Goltsev2018] or MACSima™ [@Kinkhabwala2022] can capture tumor samples' characteristics for hundreds of markers in a short time and generate large image stacks. Each image in a stack covers the spatially resolved intensity profile of a specific cell surface marker. Typically, all cells in a tissue sample slice are categorized – for example, into cancer and immune cells – based on the cell surface marker intensities on each cell. However, with ever-growing large datasets, scientific analysis of these image stacks is only feasible with machine learning.

Generating training datasets for machine learning is time-consuming and cumbersome because current software does not integrate synchronized viewing, editing, and annotation of multiple images. While it is possible to edit cell segments in CellProfiler [@Carpenter2006], only a single channel can be evaluated simultaneously. FIJI [@Schindelin2012] displays several immune images in parallel, but the different views on the images are not synchronized. An annotation or change of a cell segment must be performed in each window individually, but finding the exact location of a single cell in all images is cumbersome. Applications like ilastik [@Sommer2011] or CellPose [@Stringer2021]  fuse the analysis of images with the training of a machine learning model. However, a user can evaluate only one image at a time, and the generated data is not viable for subsequent model training.

We used InspectorCell to manually analyze cells in multiplexed immunofluorescence microscopy images of an ovarian cancer tissue slice obtained with the MACSima™ imaging platform. The tissue was stained with 99 cell markers, and a subset of the dataset is freely available[^1]. An initial cell segmentation was generated with CellProfiler and imported into InspectorCell. The cell segmentations were refined, and the cell marker expressions were quantified (fig. \autoref{fig:featandflow}a). In the initial CellProfiler segments were 1960 cells, and after refinement with InspectorCell, only 1750 cells remained. Among the immunological analysis results, we obtained a ground truth training dataset for subsequent model training, e.g., for continuous training of the CellPose model.

A synchronized overview over multiple images with editing capabilities for single-cell segmentation and quantification made this manual analysis possible. With InspectorCell, we provide a solution for efficient manual segmentation and annotation of large image stacks. The primary benefit of InspectorCell is the ability to view cells within the context of multiple cell markers, which accelerates manual analysis of cells in large image stacks. Expert immunologists can use InspectorCell to evaluate various cell characteristics at a glance and simultaneously generate high-quality training data.

[^1]: Ovarian Cancer Dataset at Synapse.org: [https://doi.org/10.7303/syn37910913.2](https://doi.org/10.7303/syn37910913.2)

# Figures

![Exemplary use cases of InspectorCell. A cell segmentation of an image stack is opened with InspectorCell. (a) Six immunofluorescence images of the image stack are displayed side-by-side in a 3×2 grid. Cell segments are displayed as blue polygons (top). A synchronized multi-cursor (orange) is a visual anchor in all channels. The CD3 channel (lower middle) is enlarged below the main window. The cell segment annotation is editable and displayed for the active cell segment in green font. (b) Over-segmentation can be merged with a single keystroke after mouse selection. (c) A cell segment (light blue) can be edited to embrace the marker signal area attributable to a distinct cell. Multiple segments can enclose the same areas to reflect cell overlaps and interactions. The manual edits of cell segmentations and annotations are saved in a single JSON file. Additionally, the JSON file can store extracted cell features, for example, mean pixel intensities.
\label{fig:featandflow}](doc/fig/featandflowS.svg.png){ width=95% }

# Acknowledgements

We thank Ali Kinkhabwala for his help during development, Bianca Heemskerk for releasing the data, Paurush Praveen, Werner Müller and Achim Tresch for reviewing the manuscript.
This project was partially funded by Miltenyi Biotec B.V. & Co. KG.

# References

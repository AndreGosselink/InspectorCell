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
  - name: Institute of Medical Statistics and Computational Biology, University of Cologne,
Bachemer Str. 86, 50931 Cologne, Germany
    index: 1
  - name: R&D Department, Miltenyi Biotec B.V. & Co. KG,
Friedrich Ebert Straße 68, 51429 Bergisch Gladbach, Germany
    index: 2
  - name: Center for Integrative Bioinformatics Vienna, Max Perutz Labs, University of Vienna, Medical University of Vienna, Dr. Bohr Gasse 9, 1030 Vienna, Austria
    index: 3
  - name: Faculty of Computer Science, University of Vienna, Währinger Str. 29, 1090 Vienna, Austria
    index: 4
date: 05 October 2022
bibliography: paper.bib

---

# Summary

Multiplexed immunofluorescence microscopy produces large image stacks of immunologic
tissue sections. Cells in these stacks can be segmented and classified by supervised
machine learning methods. However, training these models requires high-quality labeled
datasets. With recent increases in image stack sizes, the generation of labeled datasets
for supervised machine learning has become a major bottleneck. InspectorCell alleviates
this bottleneck by providing an intuitive, graphical interface for synchronized manual
segmentation and annotation of cells in highly multiplexed microscopy images.
The modular implementation of InspectorCell in Python enables tight integration into
existing applications such as Orange3 or CellProfiler. A image dataset with exampelary
annotations is available at: https://doi.org/10.7303/syn37910913.2

# Statement of need

The cellular composition of tumors is of great scientific interest as the presence
of tumor-infiltrating lymphocytes correlates with the survival of cancer patients
[@Idos2020; @Santoiemma2015]. The cellular phenotypes can be investigated
with multiplexed tissue imaging methods such as CODEX [@Goltsev2018] or MACSima$^{TM}$
[@kinkhabwalaMACSimaImagingCyclic2022]. These techniques generate large stacks
of images of the same tissue slice, where each image covers the intensity profile of a
different marker. Segmentation then enables single-cell analysis to identify cell types
by spatially co-localized markers. Once the datasets are segmented and annotated for the
presence of the markers, they can be used in supervised machine learning for feature
extraction and classification tasks. Nevertheless, this workflow has a bottleneck already
in generating segmented and annotated training data because current software does not
provide synchronized viewing, editing, and annotation of multiple images.

While it is possible to edit cell segments in CellProfiler [@Carpenter2006], only a single
channel can be evaluated simultaneously. In FIJI [@Schindelin2012] cells can be
annotated when several immune staining images are displayed in parallel. However, the
different views of the sample are not synchronized. An annotation or change
of a cell segment must be performed in each window individually, but finding the same
location on all images is very difficult. In ilastik [@Sommer2011]
the generation of training datasets are fused to the training of a machine learning
classifier. However, the user can evaluate only one image at a time and therefore misses
information necessary for annotation. Hence, a synchronized overview of all channels of
the image stack is crucial for evaluating or editing a cell segmentation. Such an overview
is also needed for annotating the localized marker expression as high or low intensity
for each image of the stack. With InspectorCell we provide a solution for efficient manual
segmentation and annotation of large image stacks. The modular implementation in Python 3
enables extension to existing software solutions such as CellProfiler.

The primary benefit of using InspectorCell is the ability to view cells within the
context of multiple immunomarkers. It accelerates manual segmentation and annotation of cells in multiplexed immunoflu-
orescence images. Expert immunologists can use it to evaluate immunological and morphological
information of cells at a glance to rapidly generate high-quality cell segmentations with annotations.
This can be saved as a JSON file for downstream applications or stored in databases.
The application addresses the need for software solutions to generate ground truth training datasets
of highly multiplexed immunofluorescence images. InspectorCell accelerates the ad-hoc creation of
high-quality training and validation datasets needed in biological image analysis by machine learning.

# Results
 We used InspectorCell to generate an exemplary training dataset from multiplexed immunofluorescence
microscopy images of an ovarian cancer tissue section, obtained with the MACSimaTM imaging platform
2
(Miltenyi Biotec B.V. & Co. KG). The tissue was stained with Hoechst and 98 antibodies against various
cluster of differentiation (CD) proteins, conjugated with phycoerythrin. For the generation of the
training dataset CD103, CD3, CD326, CD4, CD45, and CD8 were evaluated. A pixel-based segmentation
map (see Supplementary Material A) was generated with CellProfiler. The immunofluorescence images
and segmentations were imported into InspectorCell (fig. 1a, and Supplementary Material B).
A typical problem in the CellProfiler output was oversegmentation, which was corrected with Inspec-
torCell by merging (fig. 1b). Furthermore, some segments were extended to encompass the complete
area of distinctly stained cells (fig. 1c). Finally, annotations were directly applied to the cell segments,
using keyboard shortcuts. The segmentation map that resulted from this workflow was compared to the
initial CellProfiler segmentation. From the initial 1960 segments, only 1750 remained after correction.
Thus, at least 10 % of the segments in this example have originally been over-segmented. Since we elimi-
nated the bias of oversegmentation, we anticipate better performance in machine learning applications
with our InspectorCell derived ground truth dataset than with the original oversegmented single cell
data as a training dataset.


# Citations

Citations to entries in paper.bib should be in
[rMarkdown](http://rmarkdown.rstudio.com/authoring_bibliographies_and_citations.html)
format.

If you want to cite a software repository URL (e.g. something on GitHub without a preferred
citation) then you can do it with the example BibTeX entry below for @fidgit.

For a quick reference, the following citation commands can be used:
- `@author:2001`  ->  "Author et al. (2001)"
- `[@author:2001]` -> "(Author et al., 2001)"
- `[@author1:2001; @author2:2001]` -> "(Author1 et al., 2001; Author2 et al., 2002)"

# Figures

Figures can be included like this:
![Caption for example figure.\label{fig:example}](figure.png)
and referenced from text using \autoref{fig:example}.

Figure sizes can be customized by adding an optional second parameter:
![Caption for example figure.](figure.png){ width=20% }

# Acknowledgements

We thank Ali Kinkhabwala for his help during development, Bianca Heemskerk for releasing the data, Paurush Praveen, Werner Müller and Achim Tresch for reviewing the manuscript.
This project was partially funded by Miltenyi Biotec B.V. & Co. KG.

# References

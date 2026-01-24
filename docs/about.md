# About 
[![DOI](https://zenodo.org/badge/503896983.svg)](https://zenodo.org/badge/latestdoi/503896983)
## Developers

Bjoern O. Forsberg

<a href="https://twitter.com/bforsb" title="Bjoern on twitter">:fontawesome-brands-twitter:{ .twitter }</a>
<a href="https://orcid.org/0000-0002-6247-4063" title="Bjoern on ORCiD">:fontawesome-brands-orcid:{ .orcid }</a>
<a href="https://scholar.google.com/citations?user=8skHcycAAAAJ&hl=en" title="Bjoern on 
google scholar">:fontawesome-solid-graduation-cap:{ .scholar }</a>
<a href="https://github.com/bforsbe" title="Bjoern on github">:fontawesome-brands-github:{ .github }</a>
<a href="mailto:bjorn.forsberg@liu.se" title="email Bjoern">:fontawesome-solid-envelope:{ .mail }</a>
<br>

Pranav Shah

<a href="https://twitter.com/proteincapsid" title="Pranav on twitter">:fontawesome-brands-twitter:{ .twitter }</a>
<a href="https://orcid.org/0000-0003-1212-904X" title="Pranav on ORCiD">:fontawesome-brands-orcid:{ .orcid }</a>
<a href="https://scholar.google.com/citations?user=2eLXZFsAAAAJ&hl=en&oi=sra" title="Pranav on 
google scholar">:fontawesome-solid-graduation-cap:{ .scholar }</a>
<a href="https://github.com/shahpnmlab" title="Pranav on github">:fontawesome-brands-github:{ .github }</a>
<br>

Alister Burt 

<a href="https://twitter.com/AlisterBurt" title="Alister on twitter">:fontawesome-brands-twitter:{ .twitter }</a>
<a href="https://scholar.google.com/citations?user=ERGSZbUAAAAJ&hl=en&oi=sra" title="Alister on 
google scholar">:fontawesome-solid-graduation-cap:{ .scholar }</a>
<a href="https://github.com/alisterburt"  title="Alister on github">:fontawesome-brands-github:{ .github }</a>

---

## Primary citation
If you find OccuPy useful for any purpose, please refer to it and formally cite the paper: 

```
@article{Forbserg2023,
author = {Forsberg, Bjoern O and Shah, Pranav NM and Burt, Alister},
doi = {https://doi.org/10.1038/s41467-023-41478-1},
journal = {Nature Communications},
title = {A robust normalized local filter to estimate compositional heterogeneity directly from cryo-EM maps},
year = {2023}
}
```
And do please read the <a href="https://www.nature.com/articles/s41467-023-41478-1" title="link to paper">paper in Nature Communications</a>.

---

## Acknowledgements  
OccuPy is deployed to [PyPi](https://pypi.org/project/OccuPy/) using [github](https://github.com/) and [github 
workflows](https://docs.github.com/en/actions/using-workflows). 

The sigmoid function originates from [Prof. Werner Antweiler](https://wernerantweiler.ca/blog.php?item=2018-11-03). 

The documentation format is [readthedocs](https://readthedocs.org/), using 
[MkDocs-material](https://squidfunk.github.io/mkdocs-material/), based on a configuration by Talley Lambert. 

OccuPy is built purely in python. At its core, it uses [numpy](https://numpy.org/), [scipy](https://scipy.org/) and 
[matplotlib](https://matplotlib.org/). 

Additional features utilize [scikit-image](https://scikit-image.org/). 

I/O is handled by [mrcfile](https://mrcfile.readthedocs.io/en/latest/index.html), and the command-line interface 
uses [typer](https://typer.tiangolo.com/). 

The GUI was built in PyQt5, using Qt5 designer. 



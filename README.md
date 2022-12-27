# crowdquake-intensity-map
Public repository for paper "Development of seismic intensity map using low-cost micro-electro-mechanical systems seismic network"
Here we provide the implementation of - used in our paper.

# Requirements
This project written in Python 3.9 version. We recommend to use Anaconda 3 (Python 3.9) for this project. Please see the dependencies below.
## Python environments
- [Anaconda 3 (Python 3.9)](https://www.anaconda.com/)
## Dependencies
- [h3-py] (https://github.com/uber/h3-py)
- [numpy](https://numpy.org/)
- [scipy](https://www.scipy.org/)
- [pandas](https://pandas.pydata.org/)
- [obspy](https://docs.obspy.org/)
- [matplotlib](https://matplotlib.org/)

# Resources
## Example
To execute code in 'draw_pga_map.ipynb', you need to unzip file './dataset/20221029_082749_kst.zip' in './dataset' directory. This file contains seismic data of Goesan Earthquake (M4.1, 2022-10-29T08:27:49+09:00).
### Code
We provide the notebook file 'draw_pga_map.ipynb' that contains the code for generate Seismic Intensity Map.


## LCIS Network metadata
We provide metadata of LCIS network that needed for generate Seismic Intensity Map. Please see the metadata in 'resources' directory.
- LCIS network coverage cells ('./resources/lcis_network_coverage_cells.json')
- LCIS Amplitude table ('./resources/table.tsv')
- LCIS sensor list ('./resources/sensor_list.tsv')

# kfm
[![PyPI version fury.io](https://badge.fury.io/py/kfm.svg)](https://pypi.python.org/pypi/kfm/)
[![PyPI license](https://img.shields.io/pypi/l/kfm.svg)](https://pypi.python.org/pypi/kfm/)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/kfm.svg)](https://pypi.python.org/pypi/kfm/)
![Maintaner](https://img.shields.io/badge/maintainer-nbwang22-blue)

kfm is a helper package that helps reorganize Keyence files and folders to make labeling and finding images
taken by the Keyence easier.
 
Here's an example of what an example Keyence folder looks like before and after using kfm.

## Before kfm

```
.
├── A01.lnk
├── B01.lnk
├── C01.lnk
├── D01.lnk
├── E01.lnk
├── F01.lnk
├── G01.lnk
├── XY01
│   ├── 2021.07.29_293T_4X_XY01_00001_CH2.tif
│   ├── 2021.07.29_293T_4X_XY01_00001_CH4.tif
│   ├── 2021.07.29_293T_4X_XY01_00001_Overlay.tif
│   └── _A01
├── XY02
│   ├── 2021.07.29_293T_4X_XY02_00001_CH2.tif
│   ├── 2021.07.29_293T_4X_XY02_00001_CH4.tif
│   ├── 2021.07.29_293T_4X_XY02_00001_Overlay.tif
│   └── _B01
├── XY03
│   ├── 2021.07.29_293T_4X_XY03_00001_CH2.tif
│   ├── 2021.07.29_293T_4X_XY03_00001_CH4.tif
│   ├── 2021.07.29_293T_4X_XY03_00001_Overlay.tif
│   └── _C01
├── XY04
│   ├── 2021.07.29_293T_4X_XY04_00001_CH2.tif
│   ├── 2021.07.29_293T_4X_XY04_00001_CH4.tif
│   ├── 2021.07.29_293T_4X_XY04_00001_Overlay.tif
│   └── _D01
├── XY05
│   ├── 2021.07.29_293T_4X_XY05_00001_CH2.tif
│   ├── 2021.07.29_293T_4X_XY05_00001_CH4.tif
│   ├── 2021.07.29_293T_4X_XY05_00001_Overlay.tif
│   └── _E01
├── XY06
│   ├── 2021.07.29_293T_4X_XY06_00001_CH2.tif
│   ├── 2021.07.29_293T_4X_XY06_00001_CH4.tif
│   ├── 2021.07.29_293T_4X_XY06_00001_Overlay.tif
│   └── _F01
├── XY07
│   ├── 2021.07.29_293T_4X_XY07_00001_CH2.tif
│   ├── 2021.07.29_293T_4X_XY07_00001_CH4.tif
│   ├── 2021.07.29_293T_4X_XY07_00001_Overlay.tif
│   └── _G01
└── key.yaml
```

## After kfm

```
.
├── pMXs-eGFP-MODC
│   ├── 2021.07.29_293T_4X_G01_pMXs-eGFP-MODC_00001_CH2.tif
│   ├── 2021.07.29_293T_4X_G01_pMXs-eGFP-MODC_00001_CH4.tif
│   └── 2021.07.29_293T_4X_G01_pMXs-eGFP-MODC_00001_Overlay.tif
├── pMXs-eGFP-WPRE
│   ├── 2021.07.29_293T_4X_F01_pMXs-eGFP-WPRE_00001_CH2.tif
│   ├── 2021.07.29_293T_4X_F01_pMXs-eGFP-WPRE_00001_CH4.tif
│   └── 2021.07.29_293T_4X_F01_pMXs-eGFP-WPRE_00001_Overlay.tif
├── pMXs-mGL
│   ├── 2021.07.29_293T_4X_A01_pMXs-mGL_00001_CH2.tif
│   ├── 2021.07.29_293T_4X_A01_pMXs-mGL_00001_CH4.tif
│   └── 2021.07.29_293T_4X_A01_pMXs-mGL_00001_Overlay.tif
├── pMXs-mGL-MODC
│   ├── 2021.07.29_293T_4X_B01_pMXs-mGL-MODC_00001_CH2.tif
│   ├── 2021.07.29_293T_4X_B01_pMXs-mGL-MODC_00001_CH4.tif
│   └── 2021.07.29_293T_4X_B01_pMXs-mGL-MODC_00001_Overlay.tif
├── pMXs-mGL-MODC_mut
│   ├── 2021.07.29_293T_4X_C01_pMXs-mGL-MODC_mut_00001_CH2.tif
│   ├── 2021.07.29_293T_4X_C01_pMXs-mGL-MODC_mut_00001_CH4.tif
│   └── 2021.07.29_293T_4X_C01_pMXs-mGL-MODC_mut_00001_Overlay.tif
├── pMXs-mGL-UbR
│   ├── 2021.07.29_293T_4X_E01_pMXs-mGL-UbR_00001_CH2.tif
│   ├── 2021.07.29_293T_4X_E01_pMXs-mGL-UbR_00001_CH4.tif
│   └── 2021.07.29_293T_4X_E01_pMXs-mGL-UbR_00001_Overlay.tif
├── pMXs-mGL-Ubi-Y-dK
│   ├── 2021.07.29_293T_4X_D01_pMXs-mGL-Ubi-Y-dK_00001_CH2.tif
│   ├── 2021.07.29_293T_4X_D01_pMXs-mGL-Ubi-Y-dK_00001_CH4.tif
│   └── 2021.07.29_293T_4X_D01_pMXs-mGL-Ubi-Y-dK_00001_Overlay.tif
├── record.json
└── unmoved
```

 
## Install
This package is on PyPI, so just:
```
pip install kfm
```

## Usage
`kfm` has a command-line interface:

```
usage: kfm [-h] [-rev | --opt group_by_options] [--ypath yaml_path] group_folder_path
```

### Required Arguments
`group_folder_path`: The path to where the group folder is. Group folders are one level above the XY folders, e.g. `group_folder_path / XY01 / *.tif`

### Optional Arguments
`--rev`: Include this argument to reverse a move. The `record.json` file generated during the move must be in the specified `group_folder_path`.

`--opt group_by_opts`: Include this argument to specify how folders are nested. This can be provided as a single option (e.g. `'cond'`) or as a list where the order of the list specifies the order of the folder nessting. For example, `--opt cond T` nests folders by `conditions / time` point whereas `--opt T cond` nests folders by `time point / condition`. The `record.json` file generated during the move must be in the specified `group_folder_path`. Posssible options are: `['none', 'XY', 'cond', 'T', 'stitch', 'Z', 'CH', 'natural']`. The 2 special ones are `'none'` and `'natural'` which can't be specified with anything else because `'none'` dumps everything in the `group_folder_path` (so no folder nesting can be specified) and `'natural'` specifies `cond XY` because they you can see images by condition then by capture point (if you have multiple capture points in the same well). 


`--ypath yaml_path`: The path to where the yaml file is that specifies the well conditions. If no `yaml_path` is given, `kfm` will look in the `group_folder_path`. Conditions **must** be specified as an array called `wells`. Here is an example yaml file:

#### 2021.08.19_key.yaml
```
wells:
  - NIL: A1-C4
  - DD: B1-C4
  - RR: C1-C4
  - puro_ctrl: D1 
```

Conditions can be overlaid over each other. In the above example, wells `A1-A4` are just `NIL`, but wells `B1-B4` are `NIL_DD`. This make it easy to overlay several conditions in the same well. In addition, single wells can be specified, such as in the example of `D1` and `puro_ctrl`. This would result in something like this after kfm was used.


```
.
├── 2021.08.12_NT_reprogram_4dpi
    ├── NIL
    ├── NIL.DD
    ├── NIL.DD.RR
    ├── puro_ctrl
    ├── record.json
    └── unmoved
```

The yaml file can be called anything, as long as it ends in `.yaml` and is found within the `yaml_path`. `yaml_path` can be the directory where the yaml file is or the actual file name. In the case where it's the directory, `kfm` will use the first `.yaml` file that it finds.

#### yaml examples

yaml files can be named different things, as long as it ends in the correct `.yaml` extension. Here's another example of a well specification yaml file:

**key.yaml**
```
# path: '/Users/Nathan/OneDrive - Massachusetts Institute of Technology/Documents - GallowayLab/instruments/data \
#        /keyence/Nathan/Degron-mGL/2021.07.29_293T_2dpt'

wells:
  - pMXs-mGL: A1-A4
  - pMXs-mGL-MODC: B1-B4
  - pMXs-mGL-MODC_mut: C1-C4
  - pMXs-mGL-Ubi-Y-dK: D1-D4
  - pMXs-mGL-UbR: E1-E4
  - pMXs-eGFP-WPRE: F1-F4
  - pMXs-eGFP-MODC: G1-G4
```

For yaml file naming, the command:

```
$ kfm ./Degron-mGL/2021.07.29_293T_2dpt
```
would work on the following yaml files:

1. `./Degron-mGL/2021.07.29_293T_2dpt/key.yaml`
2. `./Degron-mGL/2021.07.29_293T_2dpt/2021.07.29_key.yaml`


Because no yaml path is specified using the `--ypath yaml_path` arg, `kfm` will look in the specified `group_folder_path`. But the following command would only work with the first example because a specific yaml file is specified instead of a general directory to look into:

```
$ kfm ./Degron-mGL/2021.07.29_293T_2dpt/key.yaml
```

The optional `--ypath` arg is useful to reorganize multiple group folders that have the same well layout (e.g. for biological replicates). For example, the following 3 folders could be quickly reorganized with following 3 commands:

```
.
├── Degron-mGL
    ├── 2021.07.29_293T_2dpt_01
    ├── 2021.07.30_293T_2dpt_02
    ├── 2021.07.31_293T_2dpt_03
    └── key.yaml
```

```
$ kfm ./Degron-mGL/2021.07.29_293T_2dpt_01 --ypath ./Degron-mGL/

$ kfm ./Degron-mGL/2021.07.30_293T_2dpt_02 --ypath ./Degron-mGL/

$ kfm ./Degron-mGL/2021.07.31_293T_2dpt_03 --ypath ./Degron-mGL/
```

## Developer install
If you'd like to hack locally on `kfm`, after cloning this repository:
```
$ git clone https://github.com/GallowayLabMIT/kfm.git
$ cd git
```
you can create a local virtual environment, and install `kfm` in "development mode"
```
$ python -m venv env
$ .\env\Scripts\activate    (on Windows)
$ source env/bin/activate   (on Mac/Linux)
$ pip install -e .
```
After this 'local install', you can use `kfm` freely, and it will update in real time as you work.

## License
This is licensed by the [MIT license](./LICENSE). Use freely!

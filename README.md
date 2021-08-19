# keyence_file_management
[![PyPI version fury.io](https://badge.fury.io/py/kfm.svg)](https://pypi.python.org/pypi/kfm/)
[![PyPI license](https://img.shields.io/pypi/l/kfm.svg)](https://pypi.python.org/pypi/kfm/)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/kfm.svg)](https://pypi.python.org/pypi/kfm/)
![Maintaner](https://img.shields.io/badge/maintainer-nbwang22-blue)

kfm is a helper package that helps reorganize Keyence files and folders to make labeling and finding images
taken by the Keyence easier.
 
Here's an example of what an example Keyence folder looks like before and after using kfm.

<img src="/documentation_images/before_kfm.png" width="550"/>

![Example](/documentation_images/after_kfm.png)

 
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
`-rev`: Include this argument to reverse a move. The `record.json` file generated during the move must be in the specified `group_folder_path`.

`--opt [group_by_opts]`: Include this argument to specify how folders are nested. This can be provided as a single option (e.g. `'cond'`) or as a list where the order of the list specifies the order of the folder nessting. For exampple, `--opt ['cond', 'T']` nests folders by `conditions / time` point whereas `--opt ['T', 'cond']` nests folders by `time point / condition`. The `record.json` file generated during the move must be in the specified `group_folder_path`. Posssible options are: `['none', 'XY', 'cond', 'T', 'stitch', 'Z', 'CH', 'natural']`. The 2 special ones are `'none'` and `'natural'` which can't be specified with anything else because `'none'` dumps everything in the `group_folder_path` (so no folder nesting can be specified) and `'natural'` specifies `['cond', 'XY']` because they you can see images by condition then by capture point (if you have multiple capture points in the same well). 


`--ypath yaml_path`: The path to where the yaml file is that specifies the well conditions. If no `yaml_path` is given, `kfm` will look in the `group_folder_path`. Conditions **must** be specified as an array called `wells`. Here is an example yaml file:

#### 2021.08.19_key.yaml
```
wells:
  - NIL: A1-C4
  - DD: B1-C4
  - RR: C1-C4
  - puro_ctrl: D1 
```

Conditions can be overlaid over each other. In the above example, wells `A1-A4` are just `NIL`, but wells `B1-B4` are `NIL_DD`. This make it easy to overlay several conditions in the same well. In addition, single wells can be specified, such as in the example of `D1` and `puro_ctrl`.

The yaml file can be called anything, as long as it ends in `.yaml` and is found within the `yaml_path`. `yaml_path` can be the directory where the yaml file is or the actual file name. In the case where it's the directory, `kfm` will use the first `.yaml` file that it finds.

#### yaml examples

yaml files can be named different things, as long as it ends in the correct `.yaml` extension. Here's another example of a well specification yaml file:

![Example](/documentation_images/key_yaml_ex.png)

For yaml file naming, the command:

```
$ kfm ~/OneDrive\ -\ Massachusetts\ Institute\ of\ Technology/Documents\ -\ GallowayLab/instruments/data/keyence/Nathan/Reprogram/2021.08.16_NT_SlowFT_test_02/2021.08.16_NT_4dpi 
```
would work on the following yaml files:

1. 
![Example](/documentation_images/key_yaml_short_path_ex.png)

2.  
![Example](/documentation_images/key_yaml_full_path_ex.png)


Because no yaml path is specified, `kfm` will look in the specified `group_folder_path`. But the following command would only work with the first example because a specific yaml file is specified instead of a general directory to look into:

```
$ kfm ~/OneDrive\ -\ Massachusetts\ Institute\ of\ Technology/Documents\ -\ GallowayLab/instruments/data/keyence/Nathan/Reprogram/2021.08.16_NT_SlowFT_test_02/2021.08.16_NT_4dpi/key.yaml
```

The optional `--ypath` arg is useful to reorganize multiple group folders that have the same well layout (e.g. for biological replicates). For example, the following 3 folders could be quickly reorganized with following 3 command:

```
$ kfm ~/OneDrive\ -\ Massachusetts\ Institute\ of\ Technology/Documents\ -\ GallowayLab/instruments/data/keyence/Nathan/Reprogram/2021.08.16_NT_SlowFT_test/2021.08.16_NT_SlowFT_test/2021.08.16_NT_SlowFT_test_01 --ypath /OneDrive\ -\ Massachusetts\ Institute\ of\ Technology/Documents\ -\ GallowayLab/instruments/data/keyence/Nathan/Reprogram/2021.08.16_NT_SlowFT_test

$ kfm ~/OneDrive\ -\ Massachusetts\ Institute\ of\ Technology/Documents\ -\ GallowayLab/instruments/data/keyence/Nathan/Reprogram/2021.08.16_NT_SlowFT_test/2021.08.16_NT_SlowFT_test/2021.08.17_NT_SlowFT_test_02 --ypath /OneDrive\ -\ Massachusetts\ Institute\ of\ Technology/Documents\ -\ GallowayLab/instruments/data/keyence/Nathan/Reprogram/2021.08.16_NT_SlowFT_test

$ kfm ~/OneDrive\ -\ Massachusetts\ Institute\ of\ Technology/Documents\ -\ GallowayLab/instruments/data/keyence/Nathan/Reprogram/2021.08.16_NT_SlowFT_test/2021.08.16_NT_SlowFT_test/2021.08.18_NT_SlowFT_test_03 --ypath /OneDrive\ -\ Massachusetts\ Institute\ of\ Technology/Documents\ -\ GallowayLab/instruments/data/keyence/Nathan/Reprogram/2021.08.16_NT_SlowFT_test
```

![Example](/documentation_images/key_yaml_multi_group_folder_ex.png)



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

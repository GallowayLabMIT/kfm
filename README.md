# keyence_file_management
[![PyPI version fury.io](https://badge.fury.io/py/kfm.svg)](https://pypi.python.org/pypi/ansicolortags/)
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

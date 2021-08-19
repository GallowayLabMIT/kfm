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
???

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

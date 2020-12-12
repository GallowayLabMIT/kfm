from setuptools import setup

setup(
    name='Keyence File Management',
    description='Helps manage files from Keyence for the Galloway lab',
        url='https://github.com/GallowayLabMIT/keyence_file_management',
        author='Nathan B. Wang',
        author_email='nbwang22@gmail.com',
        license='MIT',
        packages=['keyence_file_management'],
        install_requires=['pyyaml'],
        zip_safe=True,
        entry_points={
        "console_scripts": [
            "kfm=keyence_file_management:entrypoint"
            ]
        }
)

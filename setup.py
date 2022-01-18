import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="kfm",
    version="1.0.4",
    author="Nathan B. Wang",
    author_email="nbwang22@gmail.com",
    description="A better way to manage Keyence-generated microscopy data",
    license='MIT',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/GallowayLabMIT/kfm",
    project_urls={
        "Bug Tracker": "https://github.com/GallowayLabMIT/kfm/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
    zip_safe=True,
    install_requires=[
        'pyyaml'
    ],
    entry_points={
        'console_scripts': [
            'kfm = kfm:entrypoint'
    ]}
)

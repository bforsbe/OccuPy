import setuptools

setuptools.setup(
    use_scm_version={"write_to": "occupy/_version.py"},
    entry_points={
        'console_scripts': ['OccuPy=occupy.occupy:app']}
)

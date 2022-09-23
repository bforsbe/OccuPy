import setuptools

setuptools.setup(
    use_scm_version={"write_to": "occupy/_version.py"},
    entry_points={
        'console_scripts': ['occupy=occupy.occupy:app','occupy_gui=occupy.occupy:app_gui']}
)

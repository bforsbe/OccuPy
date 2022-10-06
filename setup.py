import setuptools

setuptools.setup(
    use_scm_version={"write_to": "occupy_lib/_version.py"},
    entry_points={
        'console_scripts': ['occupy=occupy_lib.occupy:app','occupy_gui=occupy_lib.occupy:app_gui']},
    include_package_data=True
)

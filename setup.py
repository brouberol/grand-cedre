from setuptools import setup, find_packages

setup(
    name="grand-cedre",
    version="0.0.1",
    include_package_data=True,
    packages=find_packages(),
    # This makes sure the templates are easy to import.
    zip_safe=False,
)

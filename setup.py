import setuptools
import kotazutils


setuptools.setup(
    name="kotazutils",
    version=kotazutils.__version__,
    author=kotazutils.__author__,
    author_email=kotazutils.__email__,
    description=kotazutils.__description__,
    long_description=kotazutils.__description__,
    long_description_content_type="text/plaintext",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)

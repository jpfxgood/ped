from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("VERSION", "r") as fh:
    version = fh.read().strip()

setup(
    name='ped-editor',
    version=version,
    url='http://github.com/jpfxgood/ped',
    author="James Goodwin",
    author_email="ped-editor@jlgoodwin.com",
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    description='A code editor written in python',
    long_description_content_type='text/markdown',
    long_description=long_description,
    license = 'MIT',
    keywords= [
        'editor',
        'ide',
    ],
    install_requires=[
        'Pygments>=2.1',
        'paramiko>=2.0.9',
    ],
    scripts=[
        'scripts/hex',
        'scripts/pyfind',
        'scripts/ped',
        'scripts/pless',
        'scripts/train_keydef',
    ],
    packages=[
        'ped_core',
        'ped_dialog',
        'ped_ssh_dialog',
        'ped_extensions',
    ],
    python_requires='>=3.6',
)

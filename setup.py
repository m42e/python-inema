from setuptools import find_packages, setup

install_requires = [
        'zeep >= 0.12.0',
        'lxml',
]

setup(
        name='inema',
        version='0.1',
        description='A Python interface to the Deutsche Post Internetmarke Online Franking',
        long_description=open('README.rst').read(),
        author='Harald Welte',
        author_email='hwelte@sysmocom.de',

        install_requires=install_requires,

        package_data={'': ['data/products.json']},

        license='AGPLv3',
        classifiers=[
            'Development Status :: 4 - Beta',
            'License :: OSI Approved :: AGPLv3 License',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3',
        ],
)

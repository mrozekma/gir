from setuptools import setup, find_packages


setup(
    name='gir',
    version='0.0.0',
    url='https://github.com/mrozekma/gir',
    author='Michael Mrozek',
    author_email='git@mrozekma.com',
    license='MIT',
    install_requires=[
        'GitPython',
    ],
    entry_points={
        'console_scripts': [
            'gir=gir:curses_main',
        ],
    },
    classifiers=[
        'Environment :: Console :: Curses',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Version Control',
    ],
    packages=find_packages(),
    include_package_data=False,
    zip_safe=True,
)

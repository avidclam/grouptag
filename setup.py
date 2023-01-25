from setuptools import setup, find_packages
import grouptag

requirements = ['pandas', 'scikit-learn']

setup(
    name=grouptag.__name__,
    version=grouptag.__version__,
    author=grouptag.__author__,
    author_email=grouptag.__author_email__,
    description=grouptag.__description__,
    python_requires='>=3.8',
    license='MIT',
    keywords="pattern keyword text categorization",
    url="https://github.com/avidclam/grouptag",
    packages=find_packages(),
    # long_description = 'PENDING',
    install_requires=requirements,
    classifiers=[
        'Programming Language :: Python :: 3.8',
        'License :: OSI Approved :: MIT License',
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
)

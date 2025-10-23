from setuptools import setup, find_packages
from pathlib import Path

long_description = (Path(__file__).parent / "README.md").read_text(encoding="utf-8")

setup(
    name='bellman_tools',
    version='0.2.1',
    description='A set of tools in Python for data manipulation, database interaction, scheduling and financial analysis for Hedge Funds.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/davidbellman/bellman_tools',
    author='David Bellman',
    author_email='david.bellman@bellmancapital.com',
    license='Proprietary',
    packages=find_packages(exclude=['tests*']),
    install_requires=[
        'pandas',
        'numpy',
        'sqlalchemy>=2.0',
        'pyodbc',
        'python-dotenv',
        'flask>=2.3.0',
        'schedule',
    ],
    include_package_data=True,
    package_data={
        'bellman_tools': ['templates/*.html', 'static/*'],
    },
    python_requires='>=3.10',
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'License :: Other/Proprietary License',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        'Topic :: Database',
    ],
    zip_safe=False,
)

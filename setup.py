from setuptools import setup

setup(
	name='bellman_tools',
	version='0.01',
	description='bellman_tools',
	url='git@github.com:davidbellman/bellman_tools.git',
	author='David Bellaiche',
	author_email='david.bellman@bellmancapital.com',
	license='DBLicense',
	packages=['bellman_tools','bellman_tools.database'],
	install_requires=[
		'pandas',
		'numpy',
		'sqlalchemy<2.0',
		'pyodbc'
	],
	zip_safe=False
)
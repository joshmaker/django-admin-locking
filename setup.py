from setuptools import setup, find_packages


setup(
    name='adminlocking',
    version='1.1',
    url='https://github.com/joshmaker/django-admin-locking/',
    license='BSD',
    description='Prevents users from overwriting each others changes in Django.',
    author='Josh West',
    packages=find_packages(),
    install_requires=[],
    zip_safe=False,
    keywords=['Django', 'admin', 'locking'],
    classifiers=[]
)

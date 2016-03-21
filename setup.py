from setuptools import setup, find_packages


setup(
    name='Django Admin Locking',
    version='1.2',
    url='https://github.com/joshmaker/django-admin-locking/',
    download_url='https://github.com/joshmaker/django-admin-locking/tarball/v1.2',
    license='BSD',
    description='Prevents users from overwriting each others changes in Django.',
    author='Josh West',
    packages=find_packages(),
    install_requires=[],
    zip_safe=False,
    keywords=['Django', 'admin', 'locking'],
    classifiers=[]
)

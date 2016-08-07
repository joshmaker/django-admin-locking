from setuptools import setup, find_packages


setup(
    name='django-admin-locking',
    version='1.3',
    url='https://github.com/joshmaker/django-admin-locking/',
    download_url='https://github.com/joshmaker/django-admin-locking/tarball/v1.3',
    license='BSD',
    description='Prevents users from overwriting each others changes in Django.',
    author='Josh West',
    packages=find_packages(),
    install_requires=[],
    zip_safe=False,
    keywords=['Django', 'admin', 'locking'],
    classifiers=[]
)

from setuptools import setup, find_packages


setup(
    name='adminlocking',
    version='1.0',
    url='https://github.com/joshmaker/django-admin-locking/',
    license='BSD',
    description='Prevents users from overwriting each others changes in Django.',
    author='Josh West',
    packages=find_packages(),
    install_requires=[],
    zip_safe=False,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP',
    ]
)

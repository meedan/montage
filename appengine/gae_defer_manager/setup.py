import os
from setuptools import setup, find_packages


ROOT = os.path.abspath(os.path.dirname(__file__))

setup(
    name='gae_defer_manager',
    version='0.1',
    description='Wrapper around Google App Engine\'s deferred library to aid task management',
    long_description=open(os.path.join(ROOT, 'README.md')).read(),
    author='David Neale',
    author_email='neale.dj@gmail.com',
    maintainer='David Neale',
    maintainer_email='neale.dj@gmail.com',
    url='http://github.com/nealedj/gae_defer_manager',
    license='BSD',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ]
)

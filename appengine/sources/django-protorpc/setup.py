import os
from setuptools import setup, find_packages


ROOT = os.path.abspath(os.path.dirname(__file__))

setup(
    name='django-protorpc',
    version='0.2.2',
    description='Helps construct ProtoRPC messages from Django models',
    long_description=open(os.path.join(ROOT, 'README.md')).read(),
    author='David Neale',
    author_email='neale.dj@gmail.com',
    maintainer='David Neale',
    maintainer_email='neale.dj@gmail.com',
    url='http://github.com/nealedj/django-protorpc',
    license='BSD',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=['Django>=1.2'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ]
)

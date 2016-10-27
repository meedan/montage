import sys
import os
from distutils.sysconfig import get_python_lib

sys.path[0:0] = [
    os.path.join(os.path.dirname(__file__), 'src'),
    os.path.join(os.path.dirname(__file__), 'lib'),
    os.path.join(os.path.dirname(__file__), 'sources'),
    os.path.join(os.path.dirname(__file__), 'sources/django-protorpc'),

    # TODO: This should definitely not be necessary, unless something else is
    # badly broken.
    get_python_lib()
]

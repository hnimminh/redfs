from setuptools import setup, find_packages

AUTHOR      = u'Minh Minh'
EMAIL       = u'hnimminh@outlook.com'
NAME        = u'redfs'
DESCRIPTION = u'Pure Python3 with Gevent implement the FreeSWITCH Event Socket Protocol Client'
URL         = u'https://github.com/hnimminh/redsw'
META = {}


with open('README.md') as f:
    README = f.read()

with open('requirements.txt') as f:
    REQUIRES = f.readlines()

with open(f'{NAME.lower()}/__version__.py') as f:
    exec(f.read(), META)
VERSION = META.get('__version__', '0.0.0')


setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description_content_type='text/markdown',
    long_description=README,
    author=AUTHOR,
    author_email=EMAIL,
    url=URL,
    license='MIT',
    packages=find_packages(exclude=('tests', 'docs')),
    classifiers=[
        # 'Development Status :: 5 - Production/Stable',
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9'
    ],
    install_requires=REQUIRES
)

# python3 setup.py sdist bdist_wheel
# python3 -m twine upload dist/*

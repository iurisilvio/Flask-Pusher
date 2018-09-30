from setuptools import setup

with open('README.md') as fh:
    long_description = fh.read()

setup(
    name='Flask-Pusher',
    version='2.0.2',
    url='https://www.github.com/iurisilvio/Flask-Pusher',
    license='MIT',
    author='Iuri de Silvio',
    author_email='iurisilvio@gmail.com',
    description='Flask extension for Pusher',
    long_description=long_description,
    long_description_content_type='text/markdown',
    py_modules=['flask_pusher'],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=[
        'Flask',
        'pusher<3',
        'Flask-Jsonpify',  # for jsonp auth support
    ],
    test_suite="tests",
    tests_require=[
        'mock',
        'unittest2',
    ],
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)

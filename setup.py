from setuptools import setup

setup(
    name='Flask-Pusher',
    version='0.1.1',
    url='https://www.github.com/iurisilvio/Flask-Pusher',
    license='MIT',
    author='Iuri de Silvio',
    author_email='iurisilvio@gmail.com',
    py_modules=['flask_pusher'],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=[
        'Flask',
        'pusher',
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

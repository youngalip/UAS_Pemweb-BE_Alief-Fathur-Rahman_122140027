from setuptools import setup, find_packages

requires = [
    'pyramid',
    'SQLAlchemy',
    'psycopg2-binary',
    'pyramid_tm',
    'zope.sqlalchemy',
    'alembic',
    'waitress',
    'pyramid_debugtoolbar',
    'bcrypt',
    'PyJWT',
    'marshmallow',
]

tests_require = [
    'WebTest',
    'pytest',
]

setup(
    name='hoopsnewsid',
    version='0.0',
    description='HoopsnewsID Backend',
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Pyramid',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
    ],
    author='',
    author_email='',
    url='',
    keywords='web pyramid pylons',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    extras_require={
        'testing': tests_require,
    },
    install_requires=requires,
    entry_points={
        'paste.app_factory': [
            'main = hoopsnewsid:main',
        ],
        'console_scripts': [
            'initialize_hoopsnewsid_db = hoopsnewsid.scripts.initialize_db:main',
        ],
    },
)

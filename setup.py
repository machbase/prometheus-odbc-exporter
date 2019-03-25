from setuptools import setup, find_packages

setup(
    name='prometheus-odbc-exporter',
    version='0.1.0',
    description='ODBC Prometheus exporter',
    url='https://github.com/MACHBASE/prometheus-odbc-exporter',
    author='MACHBASE Inc.',
    author_email='support@machbase.com',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Topic :: System :: Monitoring',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
    ],
    keywords='monitoring prometheus exporter odbc',
    packages=find_packages(),
    install_requires=[
        'pyodbc',
        'prometheus-client',
    ],
    entry_points={
        'console_scripts': [
            'prometheus-odbc-exporter=prometheus_odbc_exporter:main',
        ],
    },
)

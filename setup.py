from setuptools import setup

setup(name='jsxe-tools',
      version='0.1',
      description='JSX exchange command-line tool',
      #long_description='Really, the funniest around.',
      keywords='docker jsx jsxe exchange',
      url='http://github.com/grandrew/jsxe-tools',
      author='Andrew Gryaznov',
      author_email='andrew@jsx.exchange',
      license='GPL',
      packages=['jsxe'],
      classifiers=[
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 2',
      ],
      entry_points = {
        'console_scripts': ['jsx=jsxe:main'],
      },
      install_requires=[
          'requests',
          'pyjwt'
      ],
      zip_safe=False)
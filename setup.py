from setuptools import setup

def readme():
    with open('README.rst') as f:
        return f.read()

setup(name="quiescent",
      version="0.1",
      description="A static weblog generator",
      long_description=readme(),
      url='https://github.com/NPrescott/quiescent',
      author='Nolan Prescott',
      author_email='prescott.nolan@gmail.com',
      license='GPL',
      packages=['quiescent'],
      install_requires=[
          'Jinja2 >= 2.8',
          'MarkupSafe >= 0.23',
          'mistune >= 0.7.3',
      ],
      test_suite='quiescent.tests',
      entry_points={
      'console_scripts': ['quiescent=quiescent.command_line:main']
      },
      zip_safe=False)

from setuptools import setup, find_packages

print(find_packages(exclude=['tests*']))

setup(name='sourcelyzer',
      version='0.0.1',
      description='Sourcelyzer',
      url='https://github.com/alex-dow/sourcelyzer',
      author='Alex Dow',
      author_email='adow@psikon.com',
      license='MIT',
      packages=find_packages(),
      zip_safe=False
)

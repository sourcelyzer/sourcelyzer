from setuptools import setup

setup(name='sourcelyzer',
      version='0.0.1',
      description='Sourcelyzer',
      url='https://github.com/alex-dow/sourcelyzer',
      author='Alex Dow',
      author_email='adow@psikon.com',
      license='MIT',
      package=['sourcelyzer'],
      zip_safe=False,
      install_requires=[
          'docopt',
          'colorama',
          'cherrypy',
          'requests',
          'simplejson',
          'sqlalchemy',
          'argon2_cffi',
          'psycopg2'
      ]
)

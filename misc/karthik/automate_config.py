
class AutomateConfig:

    recipients = ['prashanthellina@gmail.com',
                  'karthikbalait@gmail.com']

    python = r'C:\Python25\python.exe'

    pythonpath = r'set PYTHONPATH=C:\PythonOgre\demos;C:\procodile\src'
    
    url = 'http://ellina.homeip.net:8000/procodile/'

    pylint_cmd = '%s do_pylint.py --rcfile=pylint.rc src\\procodile\\' % python

    epydoc_cmd = '%s C:\\Python25\\Scripts\\epydoc.py --include-log -n procodile --no-frames --quiet --quiet --quiet src\\blockworld\\' % python

    nosetests_cmd = 'nosetests --with-coverage --with-doctest --cover-package=\"procodile\" -v'

    sendmail = ''

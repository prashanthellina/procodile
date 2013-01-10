
class AutomateConfig:

    recipients = ['prashanthellina@gmail.com',
                  'karthikbalait@gmail.com']

    wipy = '/home/prashanth/.wine/drive_c/Python25/python.exe'

    pythonpath = "export PYTHONPATH='C:\\PythonOgre\\demos;\
C:\\data\\code\\procodile\\checkout\\blockworld\\src'"

    url = 'http://ellina.homeip.net:8000/procodile/'

    pylint_cmd = '%s do_pylint.py --rcfile=pylint.rc src/procodile/' % wipy

    epydoc_cmd = 'epydoc --include-log -n procodile --no-frames --quiet --quiet --quiet src/blockworld/'

    nosetests_cmd = '%s /usr/local/bin/nosetests --with-coverage --with-doctest --cover-package=\"procodile\" -v' % wipy

    sendmail = '/usr/sbin/sendmail'


class AutomateConfig:

    recipients = ['prashanthellina@gmail.com',
                  'karthikbalait@gmail.com',
                  'arahul2k2@gmail.com']

    wipy = '/home/prashanth/.wine/drive_c/Python25/python.exe'

    pythonpath = "export PYTHONPATH='C:\\PythonOgre\\demos;\
C:\\automated_tests\\procodile\\src'"

    url = 'http://ellina.homeip.net:8000/procodile/'

    pylint_cmd = '%s do_pylint.py --rcfile=pylint.rc src/procodile/' % wipy

    epydoc_cmd = 'epydoc --include-log -n procodile --no-frames --quiet --quiet --quiet src/blockworld/'

    nosetests_cmd = '%s /usr/bin/nosetests --with-coverage --with-doctest --cover-package=\"procodile\" -v' % wipy

    sendmail = '/usr/sbin/sendmail'

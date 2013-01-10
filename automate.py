#!/usr/bin/env python

import os
import re
import urlparse
import datetime
import optparse

PWD = os.path.abspath('.')
DT = datetime.datetime.now().strftime('%Y%m%dT%H%M%S')

def count_occurences(items):
    types = dict.fromkeys(set(items), 0)

    for item in items:
        types[item] += 1

    return types

def main(options, config):

    # Run tests
    test_output_fname = '%s.txt' % DT
    test_output_full_fname = os.path.join('testruns', '%s' % test_output_fname)
    test_output_full_fname = os.path.abspath(test_output_full_fname)
    test_command = "%s && cd \"%s\" && %s src tests > \"%s\" 2>&1" % \
        (config.pythonpath, PWD, config.nosetests_cmd, \
        test_output_full_fname)
    status = os.system(test_command)
    test_output = open(test_output_full_fname).read()
    coverage_result = re.findall('TOTAL.*', test_output)[0]
    num_tests_ran = re.findall('Ran [0-9]+ tests in .*', test_output)[0]
    test_result = [l.strip() for l in test_output.split('\n') if l.strip()][-1]
    if options.details:
        print test_output

    # Run epydoc to generate documentation
    epydoc_url = urlparse.urljoin(config.url, 'doc/')
    epydoc_log_url = urlparse.urljoin(epydoc_url, 'epydoc-log.html')
    epydoc_command = "cd \"%s\" && %s" % (PWD, config.epydoc_cmd)
    retval = os.system(epydoc_command)
    fname = os.path.join(PWD, 'html', 'epydoc-log.html')
    e_data = re.findall('class="log-([we][a-z]+)"', open(fname).read())
    e_data = count_occurences(e_data)
    e_data = ['%s: %s' % (k,v) for k,v in e_data.iteritems()]
    e_data = ', '.join(e_data)

    # Run pylint to get code quality information
    pylint_output_fname = 'pylint_%s.txt' % DT
    pylint_output_full_fname = os.path.abspath('testruns/%s' % pylint_output_fname)
    pylint_command = "%s && cd \"%s\" && %s > %s" % \
        (config.pythonpath, PWD, config.pylint_cmd, \
        pylint_output_full_fname)
    status = os.system(pylint_command)

    pylint_output = open(pylint_output_full_fname).read()
    pylint_result = re.findall('Your code has been rated at(.*)', pylint_output)[0].strip()
    pylint_link = urlparse.urljoin(config.url, 'pylint/') + pylint_output_fname
    if options.details:
        print pylint_output

    # generate report
    test_and_converage_link = urlparse.urljoin(config.url, 'tests/') + test_output_fname
    report = generate_report(test_result, num_tests_ran,
                             coverage_result, test_and_converage_link,
                             pylint_result, pylint_link, e_data,
                             epydoc_log_url, epydoc_url)
    
    # send report mail
    dirname = os.path.basename(PWD)
    if not options.no_email:
        send_report_mail(config, dirname, test_result, report)
    else:
        print report

def generate_report(test_result, num_tests_ran,
                    coverage_result, test_and_converage_link,
                    pylint_result, pylint_link, epydoc_data,
                    epydoc_log_url, epydoc_url):

    text = '''
    Test result: %(test_result)s
    %(num_tests_ran)s

    Coverage:
    %(coverage_result)s
    
    details: %(test_and_converage_link)s

    Pylint:
    %(pylint_result)s

    details: %(pylint_link)s

    Epydoc:
    %(epydoc_data)s

    details: %(epydoc_log_url)s

    Documentation:
    details: %(epydoc_url)s
''' % locals()

    return text

def send_report_mail(config, project, test_result, text):

    mail_data_fname = '/tmp/%s.txt' % os.getpid()
    mailf = open(mail_data_fname, 'w')

    print >> mailf, 'SUBJECT: [%s] %s - %s' % (project, test_result, DT)
    print >> mailf, 'FROM: %s@ellina.homeip.net' % (project)
    print >> mailf
    print >> mailf, text

    mailf.close()

    recipients = ', '.join(config.recipients)
    r = os.system('%s -t "%s" < %s; rm -f %s' % \
                (config.sendmail, recipients, \
                mail_data_fname, mail_data_fname))

    return r

if __name__ == '__main__':
    parser = optparse.OptionParser()

    parser.add_option('-n', '--no-email', metavar='BOOL', \
        action='store_true', help='Do not send report email')
    
    parser.add_option('-d', '--details', metavar='BOOL', \
        action='store_true', help='Show detailed report')

    parser.add_option('-c', '--config', metavar='PATH', \
        help='config module', default='automate_config')

    options, args = parser.parse_args()

    config = __import__(options.config, fromlist=['AutomateConfig'])
    config = config.AutomateConfig

    main(options, config)

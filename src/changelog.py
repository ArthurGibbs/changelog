#!/usr/bin/python

import sys, subprocess, getopt, re

import ConfigParser, os
from bs4 import BeautifulSoup
from changelog.commitReader import CommitReader
from changelog.Writer import Writer
from changelog.evaluator import Evaluator
from changelog.requestWrapper import RequestWrapper

fogbugzAPI = 'https://we7.fogbugz.com/api.asp'
githubAPI = 'https://api.github.com'

fogbugz = 'https://we7.fogbugz.com/f/'
github = 'https://github.com/we7/mediagraft/commit/'

def usage(error):
    print '''Changelog
    test.py -s<commitish>|--since<commitish>

        -h  --help      This Help
        -s  --since=    Commitish to log from, Default HEAD
        -u  --until=    Commitish to log to, Default last commit
        -w  --wiki      output in wiki format
        -a  --all       use all commits
    '''
    sys.exit(error)

def readInput(argv):
    params = {'since': 'HEAD', 'until': '', 'wiki': False, 'all': False}
    try:
        opts, args = getopt.getopt(argv,"hwas:u:",["since=","until=","wiki","all"])
    except getopt.GetoptError:
        usage(2)
    for opt, arg in opts:
        if opt == ("-h", "--help"):
            usage(0)
        elif opt in ("-w", "--wiki"):
            params['wiki'] = True
        elif opt in ("-a", "--all"):
            params['all'] = True
        elif opt in ("-s", "--since"):
            params['since'] = arg
        elif opt in ("-u", "--until"):
            params['until'] = arg
    return params


def addorAppendCommit(bug, changesByBug, commit):
    commitsForBug = []
    if bug in changesByBug:
        commitsForBug = changesByBug[bug]
    commitsForBug.append(commit)
    changesByBug[bug] = commitsForBug


def ArrangeCommitsByBug(commits):
    changesByBug = {}
    for commit in commits:
        if 'closes' in commit:
            for bug in commit['closes']:
                addorAppendCommit(bug, changesByBug, commit)
        else:
            addorAppendCommit('', changesByBug, commit)

    return changesByBug

def getFogbugzToken(config, params, requestWrapper):

    url = fogbugzAPI + '?cmd=logon&email=' + config.get("fogbugz", "username") + '&password=' + config.get("fogbugz", "password")
    soup = BeautifulSoup(requestWrapper.call(url)['body'], "xml")
    try:
        token = soup.find('token').text
    except AttributeError, e:
        print 'fogbugz login error'
        exit(0)
    return token

def main(argv):

    params = readInput(argv[1:])
    params['config'] = os.path.dirname(os.path.realpath(sys.argv[0]))+ '/config.cfg'
    config = ConfigParser.ConfigParser()
    config.readfp(open(params['config']))

    requestWrapper = RequestWrapper()

    params['gitToken'] = config.get("github", "token")
    params['gitApi'] = githubAPI
    params['fogBugzToken'] = getFogbugzToken(config, params, requestWrapper)
    params['fogBugzApi'] = fogbugzAPI

    commits = CommitReader().getCommits(params)

    (commits, fogBugzNames) = Evaluator().evaluate(commits, params, requestWrapper)

    commitsByBugNumber = ArrangeCommitsByBug(commits)
    print "Generating Release notes from " + params['since'] + ' to ' + params['until']
    Writer().outputData(commitsByBugNumber, fogBugzNames, params)


if __name__ == "__main__":
    main(sys.argv)
from bs4 import BeautifulSoup
import re
import json
import requests

class Evaluator:
    def __init__(self):
        self.closesPattern = re.compile(r"(?:closes|!bug)(?::)?\s?(?:#)?([0-9A-Z\-]+)", re.IGNORECASE)
        self.changelogPattern = re.compile(r"!changelog", re.IGNORECASE)
        self.testPattern = re.compile(r'!test(?:s)?(?::)?', re.IGNORECASE|re.DOTALL)
        self.ignorePattern = re.compile(r"(!ignore)", re.IGNORECASE)

    def getJiraName(self, case, params):
        try:
            url = 'https://issues.blinkbox.com/rest/api/2/issue/' + case
            r = requests.get(url, auth=(params['jiraUsername'], params['jiraPassword']))
            j = json.loads(r.text)
            bugname = j['fields']['summary']
        except AttributeError, e:
            bugname = 'NOT-FOUND'
        except Exception, e:
            bugname = 'NOT-FOUND'
        return bugname

    def getFogBugsName(self, case, params, requestWrapper):
        try:
            url = params['fogBugzApi'] + '?cmd=search&token=' + params['fogBugzToken'] + '&q=' + case + '&cols=sTitle'
            result = requestWrapper.call(url)['body']
            bugname = BeautifulSoup(result, "xml").find('sTitle').text
        except AttributeError, e:
            bugname = 'NOT-FOUND'
        return bugname

    def getCaseName(self, case, params, requestWrapper):
        jiraPattern = re.compile(r"^(MUS.*-[0-9]+)$", re.IGNORECASE)
        numberPattern = re.compile(r"^([0-9]+)$")
        casestring = case
        if jiraPattern.match(case):
            bugname = self.getJiraName(casestring, params)
        elif numberPattern.match(case):
            if case > 20000:
                bugname = self.getFogBugsName(case, params, requestWrapper)
            else:
                casestring = params['jiraDefaultProject'] + '-' + case
                bugname = self.getJiraName(casestring, params)
        else:
            bugname = 'NOT-FOUND'

        return bugname, casestring

    def evaluate(self, commits, params, requestWrapper):
        fogBugzNames = {}
        newList = []
        for commit in commits:
            commit['ignore'] = self.ignorePattern.findall(commit['body'])
            commit['closes'] = self.closesPattern.findall(commit['body'])
            commit['changelog'] = self.changelogPattern.findall(commit['body'])

            commit['strippedBody'] = commit['body']

            commit['strippedBody'] = re.sub(self.ignorePattern, '', commit['strippedBody'])
            commit['strippedBody'] = re.sub(self.closesPattern, '', commit['strippedBody'])
            commit['strippedBody'] = re.sub(self.changelogPattern, '', commit['strippedBody'])

            if self.testPattern.search(commit['strippedBody']):
                bodyParts = re.split(self.testPattern, commit['strippedBody'], 1)
                commit['test'] = bodyParts[1]
                commit['strippedBody'] = bodyParts[0]
                commit['test'] = commit['test'].strip()

            commit['strippedBody'] = commit['strippedBody'].strip()


            if commit['closes']:
                for caseId in commit['closes']:
                    if not caseId in fogBugzNames:
                        (summary, casecode) = self.getCaseName(caseId, params,requestWrapper)
                        fogBugzNames[casecode] = summary
                        commit['closes'].append(casecode)
                        commit['closes'].remove(caseId)
                    commit['bugname'] = fogBugzNames[casecode]

            uri = params['gitApi'] + '/repos/we7/' + params['gitRepo'] + '/git/commits/' + commit['sha'] + '?access_token=' + params['gitToken']
            if requestWrapper.call(uri)['code'] == 200:
                commit['onGit'] = True
            else:
                commit['onGit'] = False

            if ((commit['changelog'] or params['all'] is True or bool(commit['closes'])) and bool(commit['merge']) is False and bool(commit['ignore']) is False):
                newList.append(commit)

        return (newList, fogBugzNames)


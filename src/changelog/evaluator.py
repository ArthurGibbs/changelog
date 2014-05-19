from bs4 import BeautifulSoup
import re

class Evaluator:
    def __init__(self):
        self.closesPattern = re.compile(r"(?:closes|!bug)(?::)?\s?(?:#)?([0-9]+)", re.IGNORECASE)
        self.changelogPattern = re.compile(r"!changelog", re.IGNORECASE)
        self.testPattern = re.compile(r'!test(?:s)?:', re.IGNORECASE|re.DOTALL)
        self.ignorePattern = re.compile(r"(!ignore)", re.IGNORECASE)

    def getCaseName(self, case, params, requestWrapper):
        url = params['fogBugzApi'] + '?cmd=search&token=' + params['fogBugzToken'] + '&q=' + case + '&cols=sTitle'
        result = requestWrapper.call(url)['body']
        try:
            bugname = soup = BeautifulSoup(result, "xml").find('sTitle').text
        except AttributeError, e:
            bugname = 'NOT-FOUND'
        return bugname

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
                        name = self.getCaseName(caseId, params,requestWrapper)
                        fogBugzNames[caseId] = name
                    commit['bugname'] = fogBugzNames[caseId]

            uri = params['gitApi'] + '/repos/we7/' + params['gitRepo'] + '/git/commits/' + commit['sha'] + '?access_token=' + params['gitToken']
            if requestWrapper.call(uri)['code'] == 200:
                commit['onGit'] = True
            else:
                commit['onGit'] = False

            if ((commit['changelog'] or params['all'] is True or bool(commit['closes'])) and bool(commit['merge']) is False and bool(commit['ignore']) is False):
                newList.append(commit)

        return (newList, fogBugzNames)


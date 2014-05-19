__author__ = 'arthur'

class Writer:
    def __init__(self):
        pass

    def wrapCode(self, commit):
        return '<WRAP  prewrap><code>' + commit + '</code></WRAP>'

    def commitsTitle(self, params):
        if params['wiki']:
            return '=== Commits ==='
        else:
            return 'Commits:'

    def testsTitle(self, params):
        if params['wiki']:
            return '=== Tests ==='
        else:
            return 'Tests:'

    def getShaLinkOrText(self, commit, params):
        if params['wiki']:
            if commit['onGit']:
                return "\t\t\t* [[" + params['gitRepoUrl'] + commit['sha'] + '|[' + commit['sha'][:5] + ']]] ' + commit['author']
            else:
                return "\t\t\t* " + commit['sha'] + ' ' + commit['author']
        else:
            return "\t\t\t* [" + commit['sha'] + '] ' + commit['author']

    def getCommitBody(self, commit, params):
        if commit['strippedBody']:
            if params['wiki']:
                return self.wrapCode(commit['strippedBody'])
            else:
                return commit['strippedBody']
        else:
            print ''

    def printCommitSection(self, commit, params):
        print (self.getShaLinkOrText(commit, params)),
        print self.getCommitBody(commit, params)

    def testSection(self, commit, params):
        if 'test' in commit:
            print (self.getShaLinkOrText(commit, params)),
            print self.wrapCode(commit['test'])


    def testsForBug(self, commits):
        printTest = False
        for commit in commits:
            if 'test' in commit:
                printTest = True
        return printTest

    def printNamedBugSection(self, bugNumber, params, commits):
        print self.commitsTitle(params)

        for commit in commits:
            self.printCommitSection(commit, params)

        if self.testsForBug(commits):
            print self.testsTitle(params)
            for commit in commits:
                self.testSection(commit, params)
        print ''

    def printUnlistedBugSection(self, bugNumber, params, commits):
        for commit in commits:
            self.printCommitSection(commit, params)
            if 'test' in commit:
                if params['wiki']:
                    print '=== Test ==='
                else:
                    print 'Test:'
                self.testSection(commit, params)
        print ''

    def printBugTitle(self, caseId, fogbugzNames, params):
        if params['wiki']:
            if fogbugzNames[caseId] != 'NOT-FOUND':
                print "======" + caseId + ' ' + fogbugzNames[caseId] + '======'
                print "Fogbugz case: " + '[[https://we7.fogbugz.com/f/cases/' + caseId + '|' + caseId + ' ' + fogbugzNames[caseId] + ']]'
            else:
                print "======" + caseId + ' ' + fogbugzNames[caseId] + '======'
        else:
            print  caseId + " " + fogbugzNames[caseId]

    def getOtherChangesTitle(self, params):
        if params['wiki']:
            return '====== Other Changes ======'
        else:
            return 'Other Changes'

    def outputData(self, changesByCase, fogbugzNames, params):
        if params['wiki'] and len(changesByCase) > 0:
            print '======= Resolved Bugz ======='
            for caseId in changesByCase.keys():
                if caseId and fogbugzNames[caseId] != 'NOT-FOUND':
                    print "\t* " + '[[#' + caseId + ' ' + fogbugzNames[caseId] + ']]'

        for caseId, commit in changesByCase.iteritems():
            if caseId == '':
                continue

            self.printBugTitle(caseId, fogbugzNames, params)
            self.printNamedBugSection(caseId, params, commit)

        if '' in changesByCase:
            print self.getOtherChangesTitle(params)
            self.printUnlistedBugSection('', params, changesByCase[''])
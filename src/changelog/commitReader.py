__author__ = 'arthur'

import re
import subprocess

class CommitReader:

    def __init__(self):
        self.commitPattern = re.compile(r"\s*(?:commit)?\s*(?P<Sha>[\w]{40})\n(?:Merge: (?P<Merge>([\w]*) ([\w]*))\n)?Author: (?P<Author>.*) <(?P<Email>[\w\-@.]*)>\nDate:\s*(?P<Date>[a-zA-Z\s]* [0-9:\s]* \+[0-9]{4})\n(?P<Body>.*)", re.DOTALL)

    def processCommit(self, commit):
        result = self.commitPattern.match(commit)
        parts = {}

        if result:
            parts['sha'] = result.group(1)
            parts['author'] = result.group(5)
            parts['body'] = result.group(8)
            parts['merge'] = result.group(2)
            return parts

        else:
            print 'Unexpected Commit format!\n', commit
            return None


    def getCommits(self, params):
        command = ["git", "log", params['since'] + '..' + params['until']]
        output = subprocess.check_output(command)
        split = str(output).split('\ncommit ')
        commits = []

        for commitString in split:
            commit = self.processCommit(commitString)
            if (commit is not None and bool(commit['merge']) is False):
                commits.append(commit)
        return commits
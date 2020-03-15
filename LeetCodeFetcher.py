#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Simeng

import json
import os
import requests
import subprocess
import argparse
from datetime import datetime

FILE_EXTENSION = {'cpp': 'cc', 'javascript':'js'}
hasAdded = set()
toBeSubmit = []
count = 0


class ProblemInfo(object):
    id = ''
    fileName = ''

    def __init__(self, id, fileName):
        self.id = id
        self.fileName = fileName


class SubmissionInfo(object):
    id = ''
    title = ''
    language = ''
    timestamp = ''
    code = ''

    def __init__(self, id, title, language, timestamp, code):
        self.id = id
        self.title = title
        self.language = language
        self.timestamp = timestamp
        self.code = code


def fetchProblems(cookie):
    ''' Return a dictionary. Key is the title, and value ProblemInfo. '''
    url = 'https://leetcode.com/api/problems/all/'
    headers = {
        'X-Requested-With': 'XMLHttpRequest',
        'Cookie': cookie
    }
    problemResponse = requests.get(url, headers=headers)
    problemJson = json.loads(problemResponse.text)
    problemMap = {}
    for problem in problemJson['stat_status_pairs']:
        problemMap[problem['stat']['question__title']] = ProblemInfo(
            problem['stat']['question_id'], problem['stat']['question__title_slug'])
    return problemMap


def getFileName(submissionInfo, problemInfoDict):
    problemInfo = problemInfoDict[submissionInfo.title]
    if submissionInfo.language not in FILE_EXTENSION.keys():
        raise Exception('Unsupported language.')
    return (str(problemInfo.id).zfill(4) + '-' + problemInfo.fileName + '.' + FILE_EXTENSION[submissionInfo.language])


def getCommitMessage(problemTitle, problemInfoDict):
    problemInfo = problemInfoDict[problemTitle]
    return ('LeetCode '+(str(problemInfo.id) + ': '+problemTitle+'.'))


def fetchSubmissions(options, problemInfoDict):
    cookie = options.cookie
    maxSubmissions = options.max_submissions
    lastkey = ''
    offset = 0
    remainSubmissions = maxSubmissions
    codePath = options.code_path

    while remainSubmissions > 0:
        submissionPerPage = 20
        if(remainSubmissions < 20):
            submissionPerPage = remainSubmissions
        url = 'https://leetcode.com/api/submissions/?offset=' + \
            str(offset) + '&limit=' + \
            str(submissionPerPage) + '&lastkey=' + lastkey
        headers = {
            'X-Requested-With': 'XMLHttpRequest',
            'Cookie': cookie
        }
        result = requests.get(url, headers=headers)
        lastkey = handleSubmissions(json.loads(
            result.text), options, problemInfoDict)
        offset += 20
        if len(lastkey) == 0:
            # submissions that have been handled before
            break
        remainSubmissions -= submissionPerPage

    for submissionInfo in reversed(toBeSubmit):
        date = str(submissionInfo.timestamp) + ' +0800'  # Your own timezone.
        # Add and submit, but not push.
        subprocess.call(['git', 'add', getFileName(
            submissionInfo, problemInfoDict)], cwd=codePath)
        subprocess.call(['git', 'commit', '--date='+date, '-m',
                         getCommitMessage(submissionInfo.title, problemInfoDict)], cwd=codePath)


def handleSubmissions(submissions, options, problemInfoDict):
    codePath = options.code_path
    submissions_dump = submissions['submissions_dump']
    lastKey = submissions['last_key']

    for submission in submissions_dump:
        statusDisplay = submission['status_display']
        if statusDisplay == "Accepted":
            # Get parameters.
            submissionInfo = SubmissionInfo(submission['id'], submission['title'], submission['lang'], datetime.fromtimestamp(submission['timestamp']).strftime(
                '%b %d %H:%M:%S %Y'), submission['code'])
            modifiedTitle = getFileName(submissionInfo, problemInfoDict)
            global hasAdded
            if modifiedTitle in hasAdded:
                continue
            filetitle = codePath + '/' + modifiedTitle

            # Generate code file.
            if not os.path.exists(codePath):
                os.makedirs(codePath)
            with open(filetitle, encoding='utf-8', mode='w+') as submission_file:
                submission_file.write(submissionInfo.code)

            global count
            count += 1

            hasAdded.add(modifiedTitle)

            global toBeSubmit
            toBeSubmit.append(submissionInfo)

    return lastKey

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--cookie', required=True,
                        help='Cookie for authentication.')
    parser.add_argument('--code_path', required=True,
                        help='Specify the directory your code is stored. It should be placed in a git repository.')
    parser.add_argument('--max_submissions', type=int, default=20,
                        help='Max recent submissions being fetched, includes failed submissions.')
    opts = parser.parse_args()
    problemInfoDict = fetchProblems(opts.cookie)
    fetchSubmissions(opts, problemInfoDict)

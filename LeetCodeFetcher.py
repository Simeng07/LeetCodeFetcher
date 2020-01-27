#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Simeng

import json
import os
import requests
import subprocess
import argparse
from datetime import datetime

FILE_EXTENSION = {'cpp': 'cc'}
hasAdded = set()
toBeSubmit = []
count = 0


class ProblemInfo(object):
    id = ''
    fileName = ''

    def __init__(self, id, fileName):
        self.id = id
        self.fileName = fileName


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


def getFileName(title, problemInfoDict):
    problemInfo = problemInfoDict[title]
    return (str(problemInfo.id).zfill(4) + '-' + problemInfo.fileName + '.cc')


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

    for submit in reversed(toBeSubmit):
        # add and submit, but not push
        title = submit["title"]
        date = submit["date"]
        subprocess.call(['git', 'add', getFileName(
            title, problemInfoDict)], cwd=codePath)
        subprocess.call(['git', 'commit', '--date='+date, '-m',
                         getCommitMessage(title, problemInfoDict)], cwd=codePath)


def handleSubmissions(submissions, options, problemInfoDict):
    codePath = options.code_path
    submissions_dump = submissions['submissions_dump']
    lastKey = submissions['last_key']

    for submission in submissions_dump:
        statusDisplay = submission['status_display']
        if statusDisplay == "Accepted":
            # get params
            title = submission['title']
            modifiedTitle = getFileName(title, problemInfoDict)
            global hasAdded
            if modifiedTitle in hasAdded:
                continue

            sid = submission['id']
            lang = submission['lang']
            timestamp = submission['timestamp']
            code = submission['code']

            if lang not in FILE_EXTENSION:
                print('Skip '+title +
                      ' because the submission\'s language is not supported.')
                continue
            filetitle = codePath + '/' + modifiedTitle

            # generate code file
            if not os.path.exists(codePath):
                os.makedirs(codePath)
            with open(filetitle, encoding='utf-8', mode='w+') as submission_file:
                submission_file.write(code)

            global count
            count += 1

            hasAdded.add(modifiedTitle)

            # ready to submit
            date = str(datetime.fromtimestamp(timestamp).strftime(
                '%b %d %H:%M:%S %Y')) + ' +0800'  # your own timezone
            global toBeSubmit
            toBeSubmit.append({"title": title, "date": date})

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

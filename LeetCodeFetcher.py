#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Simeng

import json, os, requests, subprocess, argparse
from datetime import datetime

FILE_EXTENSION = {'cpp': 'cc'}
tocPrefix = 'https://github.com/SMartQi/LeetCode/blob/master/Code/'
codeDir = '../../LeetCode/'
codePath = codeDir + 'Code' # your own folder
hasAdded = set()
toBeSubmit = []
count = 0

def fetchProblems():
    with open(filetitle, encoding = 'utf-8', mode = 'r') as problemFile:
        problemList=problemFile.read()
        problemJson=json.loads(problemList)
        problemDic={}
        for problem in problemJson['stat_status_pairs']:
            problemDic[problem['stat']['question__title']]={id: problem['stat']['id'], fileName:problem['stat']['question__title_slug']}
        return problemDic

def fetchSubmissions(options):
    cookie = options.cookie
    codePath = options.code_path
    maxSubmissions = options.max_submissions
    lastkey = ''
    offset = 0
    remainSubmissions = maxSubmissions

    while remainSubmissions > 0:
        submissionPerPage = 20
        if(remainSubmissions < 20):
            submissionPerPage = remainSubmissions
        url = 'https://leetcode.com/api/submissions/?offset=' + \
            str(offset) + '&limit=' + str(submissionPerPage) + '&lastkey=' + lastkey
        print(url)
        headers = {
            'X-Requested-With': 'XMLHttpRequest',
            'Cookie': cookie
        }

        result = requests.get(url, headers=headers)
        print(result.text)
        lastkey = handleProblem(json.loads(result.text), options)
        offset += 20
        if len(lastkey) == 0:
            # submissions that have been handled before
            break
        remainSubmissions -= submissionPerPage

    for submit in reversed(toBeSubmit):
        # add and submit, but not push
        title = submit["title"]
        modifiedTitle = title.replace(" ", "-")
        date = submit["date"]
        addCmd = 'git add "' + modifiedTitle + '.cpp"'
        subprocess.check_call(addCmd, shell = True, cwd = codePath)
        commitCmd = 'git commit --date="' + date + '" -m "' + title + '"'
        subprocess.check_call(commitCmd, shell = True, cwd = codePath)


def handleProblem(submissions, options):
    submissions_dump = submissions['submissions_dump']
    lastKey = submissions['last_key']

    for submission in submissions_dump:
        statusDisplay = submission['status_display']
        if statusDisplay == "Accepted":
            # get params
            title = submission['title']
            modifiedTitle = title.replace(" ", "-")
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
            filetitle = codePath + '/' + modifiedTitle + '.' + FILE_EXTENSION[lang]

            if not options.skipToc:
                # insert the problem into TOC
                insertStatus = insertProblemIndex(str(sid), modifiedTitle)
                if insertStatus == -1:
                    # has handeled this very submission
                    return ''
                if insertStatus == 1:
                    # has handled the same problem
                    with open(filetitle, encoding = 'utf-8', mode = 'r') as submission_file:
                        oldSubmission = f.read()
                        if oldSubmission == code:
                            # nothing changed
                            continue

            # generate code file
            if not os.path.exists(codePath):
                os.makedirs(codePath)
            with open(filetitle, encoding = 'utf-8', mode = 'w+') as submission_file:
                submission_file.write(code)

            global count
            count += 1
            print(count)

            hasAdded.add(modifiedTitle)

            # ready to submit
            date = str(datetime.fromtimestamp(timestamp).strftime('%b %d %H:%M:%S %Y')) + ' +0800' # your own timezone
            global toBeSubmit
            toBeSubmit.append({"title": title, "date": date})

    return lastKey

def insertProblemIndex(sid, problem):
    # sid
    sidFileName = codeDir + 'sid'
    if os.path.exists(sidFileName):
        with open(sidFileName, encoding = 'utf-8', mode = 'r') as f:
            result = f.read().split('\n')
            if sid in result:
                return -1
    with open(sidFileName, encoding = 'utf-8', mode = 'a+') as f:
        f.write(sid + '\n')

    # TOC
    problem = '[' + problem + '](' + tocPrefix + problem + '.cpp)  '
    TOCFileName = codeDir + 'TOC.md'
    if os.path.exists(TOCFileName):
        with open(TOCFileName, encoding = 'utf-8', mode = 'r') as f:
            result = f.read().split('\n')
            if problem in result:
                return 1
            # binary search
            low = 0
            high = len(result) - 1
            middle = int(high / 2)
            while low < middle:
                if result[middle] < problem:
                    low = middle + 1
                else:
                    high = middle
                middle = low + int((high - low) / 2)
            if result[low] < problem:
                result.insert(low + 1, problem)
            else:
                result.insert(low, problem)
            problem = '\n'.join(result)

    with open(TOCFileName, encoding = 'utf-8', mode = 'w+') as f:
        f.write(problem)

    return 0

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--cookie', required=True,
                        help='Cookie for authentication.')
    parser.add_argument('--code_path', required=True,
                        help='Specify the directory your code is stored. It should be placed in a git repository.')
    parser.add_argument('--max_submissions', type=int, help='Max recent submissions being fetched, includes failed submissions.')
    parser.add_argument('--skip_toc', default=False,
                        help='Don\'t generate table of content.')
    opts = parser.parse_args()
    fetchSubmissions(opts)

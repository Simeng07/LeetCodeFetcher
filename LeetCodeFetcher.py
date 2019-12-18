#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Simeng

import json, os, requests, subprocess
from datetime import datetime

cookie = ''
tocPrefix = 'https://github.com/SMartQi/LeetCode/blob/master/Code/'
codeDir = '../../LeetCode/'
codePath = codeDir + 'Code' # your own folder
hasAdded = set()
toBeSubmit = []
count = 0

def fetchProblems():
    lastkey = ''
    offset = 0

    while True:
        url = 'https://leetcode.com/api/submissions/?offset=' + str(offset) + '&limit=20&lastkey=' + lastkey
        headers = {
            'X-Requested-With' : 'XMLHttpRequest',
            'Cookie' : cookie
        }

        result = requests.get(url, headers = headers)
        lastkey = handleProblem(json.loads(result.text))
        offset += 20
        if len(lastkey) == 0:
            # submissions that have been handled before
            break

    for submit in reversed(toBeSubmit):
        # add and submit, but not push
        title = submit["title"]
        modifiedTitle = title.replace(" ", "-")
        date = submit["date"]
        addCmd = 'git add "' + modifiedTitle + '.cpp"'
        subprocess.check_call(addCmd, shell = True, cwd = codePath)
        commitCmd = 'git commit --date="' + date + '" -m "' + title + '"'
        subprocess.check_call(commitCmd, shell = True, cwd = codePath)


def handleProblem(submissions):
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

            filetitle = codePath + '/' + modifiedTitle + '.cpp'

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
    fetchProblems()
"""
Context logic to generate language tags from probability values
"""

import itertools
import heapq
import re
from collections import Counter, OrderedDict
from ttp import ttp
from configparser import ConfigParser


class RunSpan(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y


runList = []


def run_compute_recur(strn, curpoint, curlist):

    runstart = curpoint

    while curpoint < len(strn)-1:
        if (strn[curpoint] != strn[curpoint+1]) or strn[curpoint] == '$':
            if (((curpoint - runstart) > 1) and (strn[curpoint] == strn[runstart] or strn[curpoint] == '$' or strn[runstart] == '$')):
                if(not(((curpoint-runstart) == 2) and runstart == 0)):
                    newrun = RunSpan(runstart, curpoint)
                    newrunlist = curlist[:]
                    newrunlist.append(newrun)
                    run_compute_recur(strn, curpoint+1, newrunlist)

        curpoint += 1

    lastrun = RunSpan(runstart, curpoint)
    if ((curpoint - runstart) > 2):
        curlist.append(lastrun)
        runList.append(curlist)


def check_skips(strn, lang):
    if lang == '0':
        alter = '1'
    else:
        alter = '0'

    i = 0

    while i < len(strn)-2:

        if strn[i] == alter:
            if (strn[i+1] == alter) and (strn[i+2] == alter):
                return False
            else:
                i += 1
        i += 1

    return True


def check_CS(strn):
    global runList
    runList = []
    run_compute_recur(strn, 0, [])

    TrueRunList = []
    TrueStrnList = []

    for runset in runList:
        check = True
        check2 = True
        check3 = True
        TrueStrn = ""
        TrueStrn2 = ""

        for run in runset:
            if check is False or (check2 is False and check3 is False):
                break

            if strn[run.y] == '0':
                tosend = strn[run.x:run.y+1]
                tosend = tosend.replace("$", "0")
                check = check_skips(tosend, '0')
                TrueStrn = TrueStrn + tosend
                TrueStrn2 = TrueStrn2 + tosend

            if strn[run.y] == '1':
                tosend = strn[run.x:run.y+1]
                tosend = tosend.replace("$", "1")
                check = check_skips(tosend, '1')
                TrueStrn = TrueStrn + tosend
                TrueStrn2 = TrueStrn2 + tosend

            if strn[run.y] == '$':
                if strn[run.x] == '0':
                    tosend = strn[run.x:run.y+1]
                    tosend = tosend.replace("$", "0")
                    check = check_skips(tosend, '0')
                    TrueStrn = TrueStrn + tosend
                    TrueStrn2 = TrueStrn2 + tosend

                if strn[run.x] == '1':
                    tosend = strn[run.x:run.y+1]
                    tosend = tosend.replace("$", "1")
                    check = check_skips(tosend, '1')
                    TrueStrn = TrueStrn + tosend
                    TrueStrn2 = TrueStrn2 + tosend

                if strn[run.x] == '$':
                    tosend = strn[run.x:run.y+1]
                    tosend = tosend.replace("$", "1")
                    check3 = check3 and check_skips(tosend, '1')
                    if check3:
                        TrueStrn = TrueStrn + tosend

                    tosend = strn[run.x:run.y+1]
                    tosend = tosend.replace("$", "0")
                    check2 = check2 and check_skips(tosend, '0')
                    if check2:
                        TrueStrn2 = TrueStrn2 + tosend

        if check is True:
            if check3 is True and TrueStrn != "":
                TrueRunList.append(runset)
                TrueStrnList.append(TrueStrn)

            if check2 is True and TrueStrn2 != "":
                TrueRunList.append(runset)
                TrueStrnList.append(TrueStrn2)

    i = 0
    Purities = {}

    while i < len(TrueRunList):
        purity = 0.0

        for run in TrueRunList[i]:
            counter = (
                Counter(TrueStrnList[i][run.x:run.y+1]).most_common(1)[0])
            if counter[0] == '0':
                purity += float(float(counter[1])/float(len(TrueStrnList[i])))
            else:
                purity += float(float(counter[1])/float(len(TrueStrnList[i])))

        purity /= (float(len(TrueRunList[i]))*float(len(TrueRunList[i])))

        Purities[i] = purity

        i += 1

    if Purities:
        for item in dict_nlargest(Purities, 1):
            return (TrueRunList[item], TrueStrnList[item], Purities[item])

    else:
        return ("", "", -1)


def compute_tag(m, strn):
    global lang1
    global lang2

    strn = strn.strip()
    origstrn = strn

    encount = 0.0
    hicount = 0.0
    for ch in strn:
        if (ch == '0'):
            encount += 1
        if (ch == '1'):
            hicount += 1
        if (ch == '$'):
            hicount += 1
            encount += 1

    if (encount/len(strn)) > 0.7:
        return lang2, "-1"
    if (hicount/len(strn)) > 0.8:
        return lang1, "-1"
    else:

        count = 0
        for x, _y in m.items():
            if len(x) < 4:
                strn = strn[:count+1] + "$" + strn[count+2:]
            count += 1

        a, b, c = check_CS(strn)
        if(c == -1 or len(a) < 2):
            CMrun = b[1:-1]

            encount1 = 0
            hicount1 = 0
            for ch in CMrun:
                if (ch == '0'):
                    encount1 += 1
                if (ch == '1'):
                    hicount1 += 1
                if (ch == '$'):
                    hicount1 += 1
                    encount1 += 1

            if(encount1 > hicount1):
                return "Code mixed" + " " + lang2, "-1"
            elif (encount1 < hicount1):
                return "Code mixed" + " " + lang1, "-1"
            else:
                return "Code mixed Equal", "-1"

        else:
            strncs = ""

            for i in a:
                if i.x > 0:
                    if (strn[i.x] == '$') and (origstrn[i.x] != b[i.x]):
                        b = b[:i.x] + origstrn[i.x] + b[i.x+1:]
                        i.x += 1
                if i.y < len(b)-1:
                    if (strn[i.y] == '$') and (origstrn[i.y] != b[i.y]):
                        b = b[:i.y] + origstrn[i.y] + b[i.y+1:]
                        i.y -= 1

            for i in a:
                strncs += b[i.x:i.y+1] + "|"

            return "Code switched", strncs[:-1]


def dict_nlargest(d, n):
    return heapq.nlargest(n, d, key=lambda k: d[k])


def get_res(orig, vals):

    global lang1
    global lang1_code
    global lang2
    global lang2_code

    # read config
    config = ConfigParser()
    config.read("config.ini")
    # use config to extract language names
    config_gen = config["GENERAL"]
    # get language names by default language 1 is HINDI and language 2 is ENGLISH
    lang1 = config_gen["language_1"].upper(
    ) if config_gen["language_1"] else "HINDI"
    lang2 = config_gen["language_2"].upper(
    ) if config_gen["language_2"] else "ENGLISH"

    lang1_code = lang1.lower()[:2]
    lang2_code = lang2.lower()[:2]

    prs = ttp.Parser()

    count = 0
    mult = 0.95
    topx = 32
    dic = OrderedDict()
    origdic = OrderedDict()
    dic[1] = vals
    origdic[1] = orig

    initlist = [u"".join(seq) for seq in itertools.product("01", repeat=5)]

    alreadyExistingTweets = {}
    processedTweets = []
    finalTweetDict = OrderedDict()

    for b, c in dic.items():
        if b:
            v = OrderedDict()
            origstr = u""
            for m, _n in c.items():
                origstr = origstr + u" " + m
            # SH had to comment out following line bc of errors:
            # ne_removed = origstr.encode('ascii', 'ignore') # why
            ne_removed = origstr

            ne_removed = u' '.join(ne_removed.split())

            total_length = 0.0
            max_length = 0

            for word in ne_removed.split():
                if True:  # SH changed
                    total_length += len(word)
                    if len(word) > max_length:
                        max_length = len(word)
                    v[word] = c[word]

            initdic = {}
            curlen = 5

            for item in initlist:
                initdic[item] = 1
            for i, _j in initdic.items():
                count = 0
                for x, y in v.items():
                    if i[count] == '0':
                        initdic[i] = initdic[i]*y[lang2_code]
                    else:
                        initdic[i] = initdic[i]*y[lang1_code]

                    if count > 0 and i[count-1] != i[count]:
                        initdic[i] = initdic[i]*(1-mult)
                    else:
                        initdic[i] = initdic[i]*mult
                    count += 1

                    if count == curlen:
                        break

            top32 = initdic
            curlen = count
            wordcount = 0

            if curlen < 5:
                newdic = {}
                for x, y in top32.items():
                    newdic[x[:curlen]] = y
                top32.clear()
                top32 = newdic

            strn = u""

            for x, y in v.items():
                strn = strn + u" " + x
                if wordcount < 5:
                    wordcount += 1
                else:
                    curlen += 1
                    newdic = {}
                    for k, p in top32.items():
                        newstr = k + '0'
                        newdic[newstr] = p * y[lang2_code]

                        if newstr[curlen-1] == '0':
                            newdic[newstr] = newdic[newstr]*mult
                        else:
                            newdic[newstr] = newdic[newstr]*(1-mult)

                        newstr = k + '1'
                        newdic[newstr] = p * y[lang1_code]

                        if newstr[curlen-1] == '1':
                            newdic[newstr] = newdic[newstr]*mult
                        else:
                            newdic[newstr] = newdic[newstr]*(1-mult)

                    top32.clear()
                    for x in dict_nlargest(newdic, topx):
                        top32[x] = newdic[x]

            for item in dict_nlargest(top32, 1):

                if len(item) > 0:
                    curOrigTweet = origdic[b]
                    superOrig = curOrigTweet

                    curOrigTweet = re.sub(r"\s+", ' ', curOrigTweet.strip())
                    tweetparse = prs.parse(curOrigTweet)
                    tweetUrls = []
                    for url in tweetparse.urls:
                        for _e in range(0, (len(re.findall(url, curOrigTweet)))):
                            tweetUrls.append(url)
                        if (len(re.findall(url, curOrigTweet))) == 0:
                            tweetUrls.append(url)

                        curOrigTweet = curOrigTweet.replace(
                            url, " THIS_IS_MY_URL ")

                    # SH NEW new keep punctuation
                    curOrigTweet = curOrigTweet.replace("#", " #")
                    curOrigTweet = curOrigTweet.replace("@", " @")
                    curOrigTweet = re.sub(r"\s+", ' ', curOrigTweet.strip())

                    tweetdic = OrderedDict()

                    splitOrig = curOrigTweet.split(' ')
                    splitHT = origstr.strip().split(' ')

                    urlcount = 0
                    for word in splitOrig:
                        if word in splitHT:
                            tweetdic[word] = "OK"
                        elif '_' in word:
                            if word == "THIS_IS_MY_URL":

                                tweetdic[tweetUrls[urlcount]] = "OTHER"
                                urlcount += 1
                            elif ((word[1:] in tweetparse.tags) or (word[1:] in tweetparse.users)):
                                tweetdic[word] = "OTHER"
                            else:
                                splt = word.split('_')
                                for wd in splt:
                                    if wd in splitHT:
                                        tweetdic[wd] = "OK"
                                    else:
                                        tweetdic[wd] = "OTHER"

                        else:
                            tweetdic[word] = "OTHER"

                    splitNE = strn.strip().split(u' ')
                    newNE = []
                    newItem = ""

                    for word, tag in tweetdic.items():
                        if tag == "OK":
                            if word in splitNE:
                                reqindex = splitNE.index(word)
                                wordlist = []
                                wordlist2 = []

                                if word in wordlist:
                                    tweetdic[word] = lang1_code.upper()
                                    newItem += "1"
                                elif word in wordlist2:
                                    tweetdic[word] = lang2_code.upper()
                                    newItem += "0"
                                # new next condition:
                                elif re.match(r"\W+", word):
                                    print(word)
                                    tweetdic[word] = "OTHER"
                                elif item[reqindex] == '0':
                                    tweetdic[word] = lang2_code.upper()
                                    newItem += "0"
                                else:
                                    tweetdic[word] = lang1_code.upper()
                                    newItem += "1"
                                newNE.append(word)
                            else:
                                tweetdic[word] = "OTHER"

                    newStrn = " ".join(newNE)

                    if len(newStrn) > 0:
                        newV = OrderedDict()

                        for q, r in v.items():
                            if q in newNE:
                                newV[q] = r

                        tweettag, runs = compute_tag(newV, '$' + newItem + '$')

                        if runs != "-1":
                            runSplit = runs.split('|')
                            runs = runs[1:-1]

                        wordDict = OrderedDict()
                        runcount = 0
                        ind = 0

                        for word in tweetdic:
                            wordlabel = OrderedDict()
                            wordlabel["Label"] = tweetdic[word]

                            if tweettag == "Code mixed" + " " + lang2 or tweettag == lang2:
                                wordlabel["Matrix"] = lang2_code.upper()
                            elif tweettag == "Code mixed" + " " + lang1 or tweettag == lang1:
                                wordlabel["Matrix"] = lang1_code.upper()
                            elif tweettag == "Code mixed Equal" or tweettag == lang1:
                                wordlabel["Matrix"] = "X"
                            else:
                                if (tweetdic[word] == lang2_code.upper() or tweetdic[word] == lang1_code.upper()):
                                    ind += 1
                                    if (runs[ind-1] == '|'):
                                        runcount += 1

                                if runSplit[runcount][0] == "0":
                                    wordlabel["Matrix"] = lang2_code.upper()
                                else:
                                    wordlabel["Matrix"] = lang1_code.upper()

                            wordDict[word] = wordlabel

                        sansRT = superOrig.replace("rt", "").strip()

                        if not(newStrn in alreadyExistingTweets) and not(sansRT in alreadyExistingTweets):

                            wholeTweetDict = OrderedDict()
                            wholeTweetDict["Tweet"] = superOrig

                            wholeTweetDict["Tweet-tag"] = tweettag
                            wholeTweetDict["Word-level"] = wordDict
                            wholeTweetDict["Twitter-tag"] = "None"

                            finalTweetDict[b] = wholeTweetDict

                            alreadyExistingTweets[sansRT] = "yes"
                            alreadyExistingTweets[newStrn] = "yes"

                            processedTweets.append(b)
                        else:
                            processedTweets.append(b)

    check_tw = {}
    for t, u in origdic.items():
        if t in finalTweetDict or t in processedTweets or u in check_tw:
            continue
        else:
            wholeTweetDict = OrderedDict()
            wholeTweetDict["Tweet"] = u
            wholeTweetDict["Tweet-tag"] = "Other_Noise"
            wholeTweetDict["Word-level"] = {}
            wholeTweetDict["Twitter-tag"] = "Noise"
            check_tw[u] = True
            finalTweetDict[t] = wholeTweetDict

    final_output = ""

    for x, y in finalTweetDict.items():
        for k, v in y['Word-level'].items():
            final_output += k + '/' + v['Label'] + ' '

    return final_output

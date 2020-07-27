"""
Master code to take input, generate features, call MALLET and use the probabilities for generating language tags
"""

# !/usr/bin/python

import sys
import subprocess
import re
import os
import time
import codecs
import pickle

from utils import extractFeatures as ef
from utils import generateLanguageTags as genLangTag
from collections import OrderedDict
from configparser import ConfigParser


def readConfig():
    """
    Read config file to load global variables for the project
    """

    global language_1_dicts
    global language_2_dicts
    global memoize_dict
    global combined_dicts
    global CLASSIFIER_PATH
    global TMP_FILE_PATH
    global DICT_PATH
    global MALLET_PATH
    global dict_prob_yes
    global dict_prob_no
    global memoize_dict_file
    global verbose
    global lang1
    global lang2

    # initialize dictionary variables
    language_1_dicts = {}
    language_2_dicts = {}
    # initialize list of dictionary words
    combined_dicts = []

    # read config
    config = ConfigParser()
    config.read("config.ini")
    config_paths = config["DEFAULT PATHS"]
    config_probs = config["DICTIONARY PROBABILITY VALUES"]
    config_dicts = config["DICTIONARY NAMES"]
    config_gen = config["GENERAL"]

    # setup paths for classifier, tmp folder, dictionaries and mallet
    CLASSIFIER_PATH = config_paths["CLASSIFIER_PATH"] if config_paths["CLASSIFIER_PATH"] else os.path.join(
        os.getcwd(), 'classifiers', 'HiEn.classifier')
    TMP_FILE_PATH = config_paths["TMP_FILE_PATH"] if config_paths["TMP_FILE_PATH"] else os.path.join(
        os.getcwd(), 'tmp', '')
    DICT_PATH = config_paths["DICT_PATH"] if config_paths["DICT_PATH"] else os.path.join(
        os.getcwd(), 'dictionaries', '')
    MALLET_PATH = config_paths["MALLET_PATH"] if config_paths["MALLET_PATH"] else os.path.join(
        os.getcwd(), 'mallet-2.0.8', 'bin', 'mallet')

    # initialize probability values for the correct and incorrect language
    dict_prob_yes = config_probs["dict_prob_yes"] if config_probs["dict_prob_yes"] else 0.999999999
    dict_prob_no = config_probs["dict_prob_no"] if config_probs["dict_prob_no"] else 1E-9

    # initialize memoize_dict from file is already present else with an empty dictionary
    memoize_dict_file = config_dicts["memoize_dict_file"] if config_dicts["memoize_dict_file"] else "memoize_dict.pkl"
    if os.path.isfile(DICT_PATH + memoize_dict_file):
        with open(DICT_PATH + memoize_dict_file, "rb") as fp:
            memoize_dict = pickle.load(fp)
    else:
        memoize_dict = {}

    # by default verbose is ON
    verbose = int(config_gen["verbose"]) if config_gen["verbose"] else 1

    # get language names by default language 1 is HINDI and language 2 is ENGLISH
    lang1 = config_gen["language_1"].upper(
    ) if config_gen["language_1"] else "HINDI"
    lang2 = config_gen["language_2"].upper(
    ) if config_gen["language_2"] else "ENGLISH"

    lang_1dict_names = config_dicts["language_1_dicts"].split(
        ",") if config_dicts["language_1_dicts"] else "hindict1"
    lang_2dict_names = config_dicts["language_2_dicts"].split(
        ",") if config_dicts["language_2_dicts"] else "eng0dict1, eng1dict1"

    # initialize language_1_dict and language_2_dict with all the sub dictionaries
    for dict_names in lang_1dict_names:
        language_1_dicts[dict_names.strip()] = {}
    for dict_names in lang_2dict_names:
        language_2_dicts[dict_names.strip()] = {}


def createDicts():
    """
    Create and populate language dictionaries for Language 1 and Language 2
    """

    global language_1_dicts
    global language_2_dicts
    global combined_dicts
    global DICT_PATH
    global lang1
    global lang2

    language_1_words = []
    language_2_words = []

    # read config to get dictionary structures
    config = ConfigParser()
    config.read("config.ini")
    dict_struct = dict(config.items("DICTIONARY HIERARCHY"))

    # create language_1 dictionary
    for sub_dict in language_1_dicts:
        input_files = dict_struct[sub_dict].split(",")
        for filename in input_files:
            with open(DICT_PATH + filename.strip(), 'r') as dictfile:
                words = dictfile.read().split('\n')
                for w in words:
                    language_1_dicts[sub_dict][w.strip().lower()] = ''

            language_1_words.extend(list(language_1_dicts[sub_dict].keys()))
    print(lang1, 'dictionary created')

    # create language_2 dictionary
    for sub_dict in language_2_dicts:
        input_files = dict_struct[sub_dict].split(",")
        for filename in input_files:
            with open(DICT_PATH + filename.strip(), 'r') as dictfile:
                words = dictfile.read().split('\n')
                for w in words:
                    language_2_dicts[sub_dict][w.strip().lower()] = ''

            language_2_words.extend(list(language_2_dicts[sub_dict].keys()))
    print(lang2, 'dictionary created')

    # populate the combined word list
    combined_dicts.extend(language_1_words)
    combined_dicts.extend(language_2_words)


def dictTagging(word, tag):
    """
    Use language dictionaries to tag words
    """

    global language_1_dicts
    global language_2_dicts
    global lang1
    global lang2

    dhin, den0, den1 = 0, 0, 0

    word = word

    if word.lower() in language_1_dicts["hindict1"].keys():
        dhin = 1
    if word.lower() in language_2_dicts["eng0dict1"].keys():
        den0 = 1
    if word.lower() in language_2_dicts["eng1dict1"].keys():
        den1 = 1

    # if not den0 and not den1 and not dhin : do nothing
    if (not den0 and not den1 and dhin) or (not den0 and den1 and dhin):  # make HI
        tag = lang1[:2]

    if (not den0 and den1 and not dhin) or (den0 and not dhin):  # make EN
        tag = lang2[:2]

    # if den0 and not den1 and not dhin : subsumed
    # if den0 and not den1 and dhin : do nothing
    # if den0 and den1 and not dhin : sumsumed
    # if den0 and den1 and dhin : do nothing

    return tag


def dictLookup(word):
    """
    Check whether a word is already present in a dictionary
    """

    global combined_dicts
    word = word.lower()
    if word in set(combined_dicts):
        return True
    return False


def blurb2Dict(blurb):
    """
    Convert a str blurb to an ordered dictionary for comparison
    """

    dic2 = OrderedDict()
    wordlist = []
    for line in blurb.split("\n"):
        line = line.split("\t")
        word = line[0].split()
        tags = line[1:]

        if len(word) != 0:
            dic2[word[0]] = tags
            wordlist.append(word)

    return dic2, wordlist


def memoizeWord(mallet_output):
    """
    Update the memoize_dict with words that are recently classified by mallet
    """

    global memoize_dict

    mallet_output = blurb2Dict(mallet_output)[0]

    for word in mallet_output.keys():
        memoize_dict[word] = mallet_output[word]


def mergeBlurbs(blurb, mallet_output, blurb_dict):
    """
    Combine probabilities of words from both MALLET and dictionary outputs
    """

    global dict_prob_yes
    global dict_prob_no
    global verbose
    global lang1
    global lang2

    # convert main blurb to OrderedDict
    main_dict = OrderedDict()
    wordlist_main = []
    for line in blurb.split("\n"):
        word, tag = line.split("\t")
        main_dict[word] = tag
        wordlist_main.append([word])

    # populate dictionary based language tags with fixed probabilities for correct and incorrect
    blurb_dict = blurb_dict.replace(lang1[:2], lang1[:2].lower(
    ) + "\t" + str(dict_prob_yes) + "\t" + lang2[:2].lower() + "\t" + str(dict_prob_no))
    blurb_dict = blurb_dict.replace(lang2[:2], lang2[:2].lower(
    ) + "\t" + str(dict_prob_yes) + "\t" + lang1[:2].lower() + "\t" + str(dict_prob_no))
    blurb_dict, _wordlist_dict = blurb2Dict(blurb_dict)

    # convert mallet blurb to OrderedDict only when it isn't empty
    mallet_is_empty = 1
    if mallet_output != "":
        mallet_is_empty = 0
        blurb_mallet, _wordlist_mallet = blurb2Dict(mallet_output)

    # combining logic
    # iterate over the word list and populate probability values for tags from both dictionary and MALLET output
    for idx, word in enumerate(wordlist_main):
        current_word = word[0]
        updated_word = word
        if current_word in blurb_dict:
            updated_word.extend(blurb_dict[current_word])
            wordlist_main[idx] = updated_word
        else:
            if not mallet_is_empty:
                if current_word in blurb_mallet:
                    updated_word.extend(blurb_mallet[current_word])
                    wordlist_main[idx] = updated_word

    # convert the updated blurb to str
    blurb_updated = []
    st = ""
    for word in wordlist_main:
        st = word[0]
        for tag in word[1:]:
            st = st + "\t" + str(tag)

        st = st.strip()
        blurb_updated.append(st)
        st = ""

    blurb_updated = "\n".join(blurb_updated)

    if verbose != 0:
        print(blurb_updated, "\n---------------------------------\n")
    return blurb_updated


def callMallet(inputText, classifier):
    """
    Invokes the mallet classifier with input text and returns Main BLURB, MALLET OUTPUT and BLURB DICT
    """

    global combined_dicts
    global TMP_FILE_PATH
    global memoize_dict

    """
    DICIONARY CREATION CODE
    """
    # create a dictionary if not already created, needed when using as a library
    if len(combined_dicts) == 0:
        createDicts()

    # split words based on whether they are already present in the dictionary
    # new words go to MALLET for generating probabilities
    fixline_mallet = list(filter(lambda x: not dictLookup(x), inputText))
    fixline_dict = list(
        filter(lambda x: (x not in fixline_mallet) or (x in memoize_dict), inputText))

    # create str blurb for mallet and dictionary input
    blurb = '\n'.join(["%s\toth" % (v.strip()) for v in inputText])
    blurb_mallet = '\n'.join(["%s\toth" % (v.strip()) for v in fixline_mallet])
    dict_tags = list(map(lambda x: dictTagging(x, "oth"), fixline_dict))

    # get dict_tags from words that are already classified by mallet
    for idx, word in enumerate(fixline_dict):
        if word in memoize_dict:
            dict_tags[idx] = memoize_dict[word]

    """
    LOGIC FOR WORDS THAT ARE PRESENT IN MULTIPLE DICTIONARIES
    """
    fixline_mallet_corrections = []
    for t, w in zip(dict_tags, fixline_dict):
        # if even after dict lookup, some words are still tagged oth due to cornercase then call mallet output on those words
        if t == "oth":
            fixline_mallet_corrections.append(w)

    # update blurb_mallet
    blurb_mallet_corrections = '\n'.join(
        ["%s\toth" % (v.strip()) for v in fixline_mallet_corrections])

    # if mallet is not empty then you need to append the correction to the bottom, seperated by a \n otherwise you can just append it directly
    if blurb_mallet != "":
        blurb_mallet = blurb_mallet + "\n" + blurb_mallet_corrections
    else:
        blurb_mallet += blurb_mallet_corrections

    # remove the words from blurb_dict
    dict_tags = filter(lambda x: x != "oth", dict_tags)
    fixline_dict = filter(
        lambda x: x not in fixline_mallet_corrections, fixline_dict)

    blurb_dict = ""
    for word, tag in zip(fixline_dict, dict_tags):
        if not type(tag) == list:
            blurb_dict = blurb_dict + "%s\t%s" % (word.strip(), tag) + "\n"
        else:
            tmp_tags = "\t".join(tag)
            blurb_dict = blurb_dict + \
                "%s\t%s" % (word.strip(), tmp_tags) + "\n"

    """
    CALLING MALLET
    """
    # this checks the case when blurb_mallet only has a \n due to words being taken into blurb_dict
    if blurb_mallet != "\n":
        # open a temp file and generate input features for mallet
        open(TMP_FILE_PATH + 'temp_testFile.txt', 'w').write(blurb_mallet)
        ef.main(TMP_FILE_PATH + 'temp_testFile.txt')
        # initialize t7 to track time taken by mallet
        t7 = time.time()
        # call mallet to get probability output
        subprocess.Popen(MALLET_PATH + " classify-file --input " + TMP_FILE_PATH + "temp_testFile.txt.features" +
                         " --output " + TMP_FILE_PATH + "temp_testFile.txt.out --classifier %s" % (classifier), shell=True).wait()
        t_total = time.time()-t7
        mallet_output = open(
            TMP_FILE_PATH + 'temp_testFile.txt.out', 'r').read()
    else:
        mallet_output = ""

    # memoize the probabilities of words already classified
    memoizeWord(mallet_output)

    print("time for mallet classification", t_total, file=sys.stderr)
    return blurb, mallet_output, blurb_dict


def genUID(results, fixline):
    """
    ADDING UNIQUE IDS TO OUTPUT FILE AND FORMATTING

    where:
    fixline is input text
    results is language probabilities for each word
    """
    # NEW add unique id  to results - which separator
    uniqueresults = list(range(len(results)))
    for idx in range(len(results)):
        uniqueresults[idx] = results[idx]
        uniqueresults[idx][0] = uniqueresults[idx][0]+"::{}".format(idx)
    langOut = OrderedDict()
    for v in uniqueresults:
        langOut[v[0]] = OrderedDict()
        for ii in range(1, len(v), 2):
            langOut[v[0]][v[ii]] = float(v[ii+1])
    fixmyline = fixline
    fnewlines = list(range(len(fixmyline)))
    for vvv in range(len(fixmyline)):
        fnewlines[vvv] = fixmyline[vvv]+"::{}".format(vvv)
    ffixedline = " ".join(fnewlines)

    return ffixedline, langOut


def langIdentify(inputText, classifier):
    """
    Get language tags for sentences passed as a list

    Input : list of sentences
    Output : list of words for each sentence with the language probabilities
    """

    global TMP_FILE_PATH

    inputText = inputText.split("\n")
    outputText = []

    """
    CONFIG FILE CODE
    """
    readConfig()

    """
    DICIONARY CREATION CODE
    """
    createDicts()

    for line in inputText:
        text = re.sub(r"([\w@#\'\\\"]+)([.:,;?!]+)", r"\g<1> \g<2> ",  line)
        text = text.split()
        text = [x.strip() for x in text]
        text = [x for x in text if not re.match(r"^\s*$", x)]
        """
        CALLING MALLET CODE HERE
        """
        blurb, mallet_output, blurb_dict = callMallet(text, classifier)

        """
        WRITE COMBINING LOGIC HERE
        """
        blurb_tagged = mergeBlurbs(blurb, mallet_output, blurb_dict)

        results = [v.split("\t") for v in blurb_tagged.split("\n")]
        # generate unique id for output sentences and format
        ffixedline, langOut = genUID(results, text)
        # get language tags using context logic from probabilities
        out = genLangTag.get_res(ffixedline, langOut)
        realOut = re.sub("::[0-9]+/", "/", out)
        # get word, label pairs in the output
        realOut = realOut.split()
        realOut = [tuple(word.split("/")) for word in realOut]
        # generate output
        outputText.append(realOut)

    return outputText


def langIdentifyFile(filename, classifier):
    """
    Get language tags for sentences from an input file

    Input file: tsv with sentence id in first column and sentence in second column
    Output file: tsv with word per line, sentences separated by newline
    Output of sentence id in first column and best language tag in last column
    """
    global TMP_FILE_PATH

    # reading the input file
    fil = codecs.open(filename, 'r', errors="ignore")
    outfil = codecs.open(filename+"_tagged", 'a',
                         errors="ignore", encoding='utf-8')
    line_count = 0
    line = (fil.readline()).strip()

    while line is not None and line != "":
        line_count += 1

        if (line_count % 100 == 0):
            print(line_count, file=sys.stderr)

        if not line.startswith("#"):
            # reading sentences and basic pre-processing
            lineid = "\t".join(line.split("\t")[:1])
            line = " ".join(line.split("\t")[1:])
            fline = re.sub(r"([\w@#\'\\\"]+)([.:,;?!]+)",
                           r"\g<1> \g<2> ",  line)
            fixline = fline.split()
            fixline = [x.strip() for x in fixline]
            fixline = [x for x in fixline if not re.match(r"^\s*$", x)]

            """
            CALLING MALLET CODE HERE
            """
            blurb, mallet_output, blurb_dict = callMallet(fixline, classifier)

            """
            WRITE COMBINING LOGIC HERE
            """
            blurb_tagged = mergeBlurbs(blurb, mallet_output, blurb_dict)

            results = [v.split("\t") for v in blurb_tagged.split("\n")]

            # generate unique id for output sentences and format
            ffixedline, langOut = genUID(results, fixline)

            # get language tags using context logic from probabilities
            out = genLangTag.get_res(ffixedline, langOut)
            outfil.write(u"##"+lineid+u"\t"+line+u"\n")
            realout = re.sub("::[0-9]+/", "/", out)
            outfil.write(lineid+u"\t"+realout+u'\n')
        else:
            print("### skipped commented line:: " + line.encode('utf-8') + "\n")
            outfil.write("skipped line" + line.encode('utf-8') + "\n")
        line = (fil.readline()).strip()
    fil.close()
    outfil.close()
    print("written to " + filename + "_tagged")


def writeMemoizeDict():
    """
    Write the Memoization Dictionary to the disk, update it with new words if already present
    """

    if os.path.isfile(DICT_PATH + memoize_dict_file):
        # if file already exists, then update memoize_dict before writing
        with open(DICT_PATH + memoize_dict_file, "rb") as fp:
            memoize_file = pickle.load(fp)
            if memoize_file != memoize_dict:
                print("updating memoize dictionary")
                memoize_dict.update(memoize_file)
    # write the memoize_dict to file
    with open(DICT_PATH + memoize_dict_file, "wb") as fp:
        pickle.dump(memoize_dict, fp)


if __name__ == "__main__":

    """
    CONFIG FILE CODE
    """
    readConfig()

    """
    DICIONARY CREATION CODE
    """
    createDicts()

    """
    CLASSIFICATION CODE
    """

    blurb = sys.argv[1]
    print(blurb)
    print(sys.argv)
    classifier = CLASSIFIER_PATH
    mode = "file"

    if len(sys.argv) > 2:
        mode = sys.argv[1]
        blurb = sys.argv[2]
    if len(sys.argv) > 3:
        classifer = sys.argv[3]
    if mode == "file" or mode == "f":
        # CHECK FILE EXISTS
        langIdentifyFile(blurb, classifier)
    else:
        langIdentify(blurb, classifier)

    """
    WRITE UPDATED MEMOIZE DICTIONARY TO DISK
    """
    writeMemoizeDict()
    exit()

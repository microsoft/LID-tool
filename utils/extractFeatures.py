"""
Given a word list with language, prepare the data for input to MALLET
"""

import sys
from collections import defaultdict
import codecs


def get_ngrams(word, n):
    """
    Extracting all ngrams from a word given a value of n
    """

    if word[0] == '#':
        word = word[1:]

    if n != 1:
        word = '$'+word+'$'

    ngrams = defaultdict(int)
    for i in range(len(word)-(n-1)):
        ngrams[word[i:i+n]] += 1
    return ngrams


def main(input_file_name):
    """
    The main function
    """

    # The input file containing wordlist with language
    input_file = open(input_file_name, 'r')

    # The output file
    output_file_name = input_file_name + ".features"
    output_file = codecs.open(output_file_name, 'w', encoding='utf-8')

    # N upto which n grams have to be considered
    n = 5

    # Iterate through the input-file
    for each_line in input_file:
        fields = list(filter(None, each_line.strip().split("\t")))
        word = fields[0]
        output_file.write(word)
        output_file.write('\t')

        # Get all ngrams for the word
        for i in range(1, min(n+1, len(word) + 1)):
            ngrams = get_ngrams(word, i)
            for each_ngram in ngrams:
                output_file.write(each_ngram)
                output_file.write(':')
                output_file.write(str(ngrams[each_ngram]))
                output_file.write('\t')

        output_file.write('\n')

    input_file.close()
    output_file.close()


if __name__ == "__main__":
    input_file_name = sys.argv[1]
    main(input_file_name)

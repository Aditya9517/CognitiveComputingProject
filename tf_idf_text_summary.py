import json
import math
import re
import textwrap

from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize, sent_tokenize

# predefined max length of a sentence
S = 10

# threshold value is inversly proportional to the length of the summary
THRESHOLD_VALUE = 0.8

# text wrapper to wrap lines and indentation to each line
wrapper = textwrap.TextWrapper(initial_indent='\t', subsequent_indent='\t', width=100)

# reducing words to their root form using lemmatization
word_lemmatizer = WordNetLemmatizer()

# initializing nltk defined set of stop words for english
stop_words = set(stopwords.words("english"))


def eliminate_url_emoji(string):
    """
    function to eliminate non ascii, utf-8 characters and urls in text
    :param string: represents one review
    :return: a string
    """
    # regular expression to match emoticons, symbols, and map symbols
    emoji_pattern = re.compile("["u"\U0001F600-\U0001F64F" u"\U0001F300-\U0001F5FF" u"\U0001F680-\U0001F6FF" 
                               u"\U0001F1E0-\U0001F1FF" "]+", flags=re.UNICODE)
    input_text = emoji_pattern.sub(r'', string)
    # to eliminate urls in string
    input_text = re.sub(r'http\S+', '', input_text)
    return input_text + "\n" + "\n"


def eliminate_stopwords_stemming(text):
    """
    function eliminates stop words and returns a frequency matrix,
    the frequency matrix is a dictionary that contains key, value pairs
    in which the key represents a sentence and the value represents the count
    or frequency of occurrence.
    :param text: a collection of reviews
    :return: a word frequency matrix
    """
    # creating dictionary for the word frequency table
    word_frequency = {}

    for sentence in text:
        freq = {}
        # splitting strings based on space and punctuation
        words = word_tokenize(sentence)
        # eliminating stop words from consideration
        words = [w for w in words if w not in stop_words]
        for word in words:
            # reducing words to their root form using lemmatization
            word = word_lemmatizer.lemmatize(word)
            # increase counter if it appears more than once
            if word in freq:
                freq[word] += 1
            # if word not a key in dictionary
            else:
                freq[word] = 1
        # considering sentence lengths up to 10
        word_frequency[sentence[:S]] = freq
    return word_frequency


def summary_of_reviews(tf_idf_matrix, reviews, res_file):
    """
    generates a summary of reviews by computing a score for each review,
    score of a sentence = (term-frequency-value/length of sentence)
    average score is computed by adding all the scores and dividing it by the
    number of keys (associated with scores), a sentence is selected for text summarization
    if the sentence score is more than the product average score and threshold value,
    the threshold value is pre-defined, changing this value results in different lengths of
    a summary
    :param tf_idf_matrix: computed tf-idf dictionary
    :param reviews: original reviews are processed
    :param res_file: result file
    :return: a summary of reviews is generated
    """
    summary = ""
    scores = {}
    for sentence, frequency in tf_idf_matrix.items():
        # initialize total score for the sentence to 0
        total_score = 0
        # number of items in nested dictionary
        number_of_items = len(frequency)
        for word, score in frequency.items():
            # score represents tf-idf value
            total_score += score
        scores[sentence] = total_score / number_of_items

    res_file.write("Sentence scores are:\n\n")
    # computing average scores
    sum_scores = sum(scores.values())
    res_file.write('Sum of all scores = ' + wrapper.fill(str(sum_scores)) + '\n\n')
    average_score = sum_scores/len(scores)
    res_file.write('Average Score = ' + wrapper.fill(str(average_score)) + '\n\n')

    # generating a summary using a threshold value
    threshold_value = average_score * THRESHOLD_VALUE
    # based on testing, it was found that a higher threshold value generates a shorter summary
    res_file.write("Generating summary for threshold value: \t" + str(THRESHOLD_VALUE) + "\n\n")
    for review in reviews:
        if review[:S] in scores and scores[review[:S]] >= threshold_value:
            summary += review
    res_file.write("Summary generated is:\n\n")
    res_file.write(wrapper.fill(summary) + '\n')
    return summary


def text_summarization_using_tf_idf(all_text=None):
    with open('tf_idf_results.txt', 'w') as results_file:
        results_file.write("TF-IDF results file\n\n")
        with open('movie.txt', 'r') as test:
            all_reviews = test.readline()

            # data cleaning process
            all_reviews = eliminate_url_emoji(all_reviews)
            # convert sentences in to tokens
            sentences = sent_tokenize(all_reviews)
            # creating a dictionary for the word frequency table
            freq_of_words = eliminate_stopwords_stemming(sentences)

            # computing term frequency
            # term frequency (tf) = (no of times term appears in a document/total number of terms in document)
            # initializing term frequency matrix
            term_frequency = {}
            results_file.write("Computing Term Frequency\n\n")
            for sentence, frequency in freq_of_words.items():
                tf = {}
                total_terms_in_document = len(frequency)
                for word, terms_in_document in frequency.items():
                    tf[word] = terms_in_document / total_terms_in_document
                term_frequency[sentence] = tf

            results_file.write(wrapper.fill(json.dumps(term_frequency)) + "\n\n")

            # builds a dictionary which describes the frequency of occurrence of a word in a text or document
            number_of_documents_containing = {}
            for sentence, f_matrix in freq_of_words.items():
                for word, count in f_matrix.items():
                    if word in number_of_documents_containing:
                        # a dictionary containing {word:frequency_of_occurrence_in_a_document}
                        number_of_documents_containing[word] += 1
                    else:
                        # initialize frequency count to 1, if word does not exist in dictionary
                        number_of_documents_containing[word] = 1

            # computing inverse document frequency
            # inverse document frequency (idf) = log(total no of documents/number of documents containing the term)
            # initializing inverse document frequency
            results_file.write("Computing inverse document frequency\n\n")
            inverse_document_frequency = {}
            # a word frequency matrix
            for sentence, freq_matrix in freq_of_words.items():
                inverse_doc_freq = {}
                for word in freq_matrix.keys():
                    inverse_doc_freq[word] = math.log(len(sentences) / float(number_of_documents_containing[word]),
                                                      10)
                inverse_document_frequency[sentence] = inverse_doc_freq

            results_file.write(wrapper.fill(json.dumps(inverse_document_frequency)) + "\n\n")

            # computing tf-idf matrix
            # function to compute tf-idf, tf-idf describes how important a word is in a collection of documents
            # high f-idf value is proportional to the number of times a word appears in a document.
            term_freq_inverse_doc_freq_matrix = {}
            results_file.write("Computing term frequency * inverse document frequency\n\n")
            for (x1, y1), (x2, y2) in zip(term_frequency.items(), inverse_document_frequency.items()):
                tf_idf = {}
                for (x3, y3), (x4, y4) in zip(y1.items(), y2.items()):
                    tf_idf[x3] = float(y3) * float(y4)
                term_freq_inverse_doc_freq_matrix[x1] = tf_idf
                # print(term_freq_inverse_doc_freq_matrix)

            results_file.write(wrapper.fill(json.dumps(term_freq_inverse_doc_freq_matrix)) + "\n\n")

            # original text
            results_file.write("Original file content" + "\n\n")
            results_file.write(wrapper.fill(all_reviews) + "\n\n")
            # generate summary
            summary_of_movie_reviews = summary_of_reviews(term_freq_inverse_doc_freq_matrix, sentences,
                                                          results_file)
            print(summary_of_movie_reviews)


if __name__ == '__main__':
    # read_from_file = False
    #
    # if read_from_file:
    #     # reads from json file
    #     with open('movie_sampled_data.json', 'r') as f:
    #         movie_file = json.load(f)
    #     # for each movie perform text summarization on all the reviews
    #     for movie_name in movie_file:
    #         text = ""
    #         for j in movie_file[movie_name]:
    #             text += eliminate_url_emoji(j['review'])
    #         text_summarization_using_tf_idf(text)
    #         break

    text_summarization_using_tf_idf()

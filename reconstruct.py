import numpy as np
import sys
import logging

def levenshtein(needle, haystack, case_sensitive = True, substring_match = "full"):
    # substring_match
    # full
    # substring
    # beginning
    # end
    assert substring_match in ["full", "substring", "beginning", "end"]


    size_x = len(needle) + 1
    size_y = len(haystack) + 1

    # ignore cases
    if not case_sensitive:
        needle = needle.lower()
        haystack = haystack.lower()

    matrix = np.zeros ((size_x, size_y))
    for x in range(size_x):
        matrix [x, 0] = x
    for y in range(size_y):
        if substring_match in ["substring", "end"]:
            matrix [0, y] = 0 # ignore prefix that doesn't match
        else:
            matrix [0, y] = y # full levenstein
        

    for x in range(1, size_x):
        for y in range(1, size_y):
            if needle[x-1] == haystack[y-1]:
                matrix [x,y] = min(
                    matrix[x-1, y] + 1,
                    matrix[x-1, y-1],
                    matrix[x, y-1] + 1
                )
            else:
                matrix [x,y] = min(
                    matrix[x-1,y] + 1,
                    matrix[x-1,y-1] + 1,
                    matrix[x,y-1] + 1
                )
    #print (matrix)

    if substring_match in ["substring", "beginning"]:
        return min(matrix[size_x - 1]) # early stop
    else:
        return (matrix[size_x - 1, size_y - 1]) # full levenstein

# check correct arguments
if len(sys.argv) < 2:
    logging.error("Usage: {} documents_two_columns sentence_split \n Where documents_two_columns has first column of IDs, second of documents".format(sys.argv[0]))
    sys.exit(0)


original_docs = []
with open(sys.argv[1]) as orig:
    for line in orig:
        out = line.rstrip('\r\n').split('\t')
        assert len(out) == 2, "document doesn't contain two columns at line {}".format(len(original_docs))
        original_docs.append(out)

all_sentences = []
with open(sys.argv[2]) as tokenized:
    for line in tokenized:
        possible = {"line": line.rstrip('\r\n'), "distance": {}} # no distance has been computed yet.
        all_sentences.append(possible)

# THEOREM: sum of sentence distances to given document is lower or equal than distance of concatenated sentences and given document

lowest_possible_docid = 0
highest_possible_docid = 0
reconstructed_document = []

for sentence_id in range(len(all_sentences)):
    sentence = all_sentences[sentence_id]
    # ASSUMPTION: there is no sentence removed, each document contain at least one sentence
    highest_possible_docid += 1

    counter = 0
    for i in range(highest_possible_docid + 1):
        if lowest_possible_docid <= i < len(original_docs):
            if i not in sentence['distance']:
                # compute sentence to docs distance
                counter += 1
                sentence['distance'][i] = levenshtein(sentence['line'], original_docs[i][1], False, "substring")

    # remove documents that has much worst distance than the best
    closest_docid = next(iter({k: v for k, v in sorted(sentence['distance'].items(), key=lambda item: item[1])}))
    distance_length_ratio = sentence['distance'][closest_docid] / len(sentence['line'])
    if len(sentence['line']) > 20 and distance_length_ratio < 0.2: # minimum 20 characters to be sure
        for docid in list(sentence['distance'].keys()): # necessary to allow deletion of keys
            if sentence['distance'][docid] / len(sentence['line']) > distance_length_ratio + 0.5:
                del sentence['distance'][docid]

    # update lowest and highest possible docid
    lowest_possible_docid = min(sentence['distance'].keys())
    highest_possible_docid = max(sentence['distance'].keys())

    if lowest_possible_docid == highest_possible_docid:
        # remove from previous sentences any higher docid as it is not possible since we got docid confirmed
        for i in range(sentence_id):
            for d in list(all_sentences[i]['distance'].keys()):
                if d > lowest_possible_docid:
                    del all_sentences[i]['distance'][d]


# reconstruct documents
reconstructed_document = []
previous_docid = 0
counter = 0
for sentence_id in range(len(all_sentences)):
    sentence = all_sentences[sentence_id]

    if sentence_id == 0:
        # first sentence must be in first document
        decision = 0
    elif sentence_id == len(all_sentences) - 1:
        # last sentence must be in last document
        decision = len(original_docs) - 1
    elif len(sentence['distance']) == 1:
        # there is exact match
        decision = next(iter(sentence['distance']))
    else:
        # if minimal docid is bigger than previous docid, it must be it
        minimal_docid = min(sentence['distance'])
        if minimal_docid > previous_docid:
            assert previous_docid - 1 == minimal_docid, "There is missing document"
            decision = previous_docid
        elif previous_docid + 1 not in sentence['distance']:
            # this means that next document was discarded
            decision = previous_docid
        else:
            assert previous_docid in sentence['distance'], "In this step, previous docid should be among distances"
            # compute distance with previous sentence and following sentence, decide which is closer
            with_previous = all_sentences[sentence_id - 1]['line'] + " " + sentence['line']
            with_following = sentence['line'] + " " + all_sentences[sentence_id + 1]['line']

            # we don't know if investigated sentence is last/first (although it is often the case)
            dist_with_previous = levenshtein(with_previous, original_docs[previous_docid][1], False, "substring")
            dist_with_following = levenshtein(with_following, original_docs[previous_docid + 1][1], False, "substring")

            # if the difference is small, inform for manual check
            distance_when_added_to_previous = dist_with_previous - all_sentences[sentence_id - 1]['distance'][previous_docid]
            distance_when_added_to_following = dist_with_following - all_sentences[sentence_id + 1]['distance'][previous_docid + 1]
            difference_in_ratio = abs(distance_when_added_to_previous  -  distance_when_added_to_following) / len(sentence['line'])
            if difference_in_ratio < 0.5:
                logging.warning("Small difference in length ratio ({} %) on sentence bordering documents '{}' and '{}'. Check manually".format(difference_in_ratio*100, original_docs[previous_docid][0], original_docs[previous_docid + 1][0]))

            if distance_when_added_to_previous < distance_when_added_to_following:
                decision = previous_docid
            else:
                decision = previous_docid + 1


    if previous_docid < decision:
        assert previous_docid + 1 == decision, "There is a skipped document, investigate document after {}".format(original_docs[previous_docid][0])
        previous_docid = decision
        counter = 0

    # we should find most possible start in document and most possible end and crop that
    print("{}\t{}\t{}".format(original_docs[previous_docid][0], counter, sentence['line']))
    counter += 1



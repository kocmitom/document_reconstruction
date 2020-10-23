# Fuzzy document reconstruction

This script is useful for reconstruction of a document from individual sentences when those have been modified (cleaned). It relies on levenshtein distance of substrings. 

It takes two files as an input: original document with arbitrary doc_IDs and file with individual modified sentences.
Script returns sentences with original doc_ids, sentence number in document, and sentence.

Assumptions:
Sentences are in the same order as in original documents. But they can be modified (capitalization, punctuation, removal of words, etc).

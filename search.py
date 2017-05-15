# Copyright 2017 Nolan Prescott
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import re

stopwords = set(["a", "about", "above", "across", "after", "afterwards",
                 "again", "against", "all", "almost", "alone", "along", "already", "also",
                 "although", "always", "am", "among", "amongst", "amoungst", "amount", "an",
                 "and", "another", "any", "anyhow", "anyone", "anything", "anyway", "anywhere",
                 "are", "around", "as", "at", "back", "be", "became", "because", "become",
                 "becomes", "becoming", "been", "before", "beforehand", "behind", "being",
                 "below", "beside", "besides", "between", "beyond", "bill", "both", "bottom",
                 "but", "by", "call", "can", "cannot", "cant", "co", "computer", "con", "could",
                 "couldnt", "cry", "de", "describe", "detail", "do", "done", "down", "due",
                 "during", "each", "eg", "eight", "either", "eleven", "else", "elsewhere",
                 "empty", "enough", "etc", "even", "ever", "every", "everyone", "everything",
                 "everywhere", "except", "few", "fifteen", "fify", "fill", "find", "fire",
                 "first", "five", "for", "former", "formerly", "forty", "found", "four", "from",
                 "front", "full", "further", "get", "give", "go", "had", "has", "hasnt", "have",
                 "he", "hence", "her", "here", "hereafter", "hereby", "herein", "hereupon",
                 "hers", "herself", "him", "himself", "his", "how", "however", "hundred", "i",
                 "ie", "if", "in", "inc", "indeed", "interest", "into", "is", "it", "its",
                 "itself", "keep", "last", "latter", "latterly", "least", "less", "ltd", "made",
                 "many", "may", "me", "meanwhile", "might", "mill", "mine", "more", "moreover",
                 "most", "mostly", "move", "much", "must", "my", "myself", "name", "namely",
                 "neither", "never", "nevertheless", "next", "nine", "no", "nobody", "none",
                 "noone", "nor", "not", "nothing", "now", "nowhere", "of", "off", "often", "on",
                 "once", "one", "only", "onto", "or", "other", "others", "otherwise", "our",
                 "ours", "ourselves", "out", "over", "own", "part", "per", "perhaps", "please",
                 "put", "rather", "re", "same", "see", "seem", "seemed", "seeming", "seems",
                 "serious", "several", "she", "should", "show", "side", "since", "sincere",
                 "six", "sixty", "so", "some", "somehow", "someone", "something", "sometime",
                 "sometimes", "somewhere", "still", "such", "system", "take", "ten", "than",
                 "that", "the", "their", "them", "themselves", "then", "thence", "there",
                 "thereafter", "thereby", "therefore", "therein", "thereupon", "these", "they",
                 "thick", "thin", "third", "this", "those", "though", "three", "through",
                 "throughout", "thru", "thus", "to", "together", "too", "top", "toward",
                 "towards", "twelve", "twenty", "two", "un", "under", "until", "up", "upon",
                 "us", "very", "via", "was", "we", "well", "were", "what", "whatever", "when",
                 "whence", "whenever", "where", "whereafter", "whereas", "whereby", "wherein",
                 "whereupon", "wherever", "whether", "which", "while", "whither", "who",
                 "whoever", "whole", "whom", "whose", "why", "will", "with", "within",
                 "without", "would", "yet", "you", "your", "yours", "yourself", "yourselves"])

def interesting_words(text):
    only_alpha = re.sub(r'[^A-Za-z]', ' ', text)
    single_space = re.sub(r'\s+', ' ', only_alpha)
    words = single_space.split()
    unique_lowercase_words = {word.lower() for word in words}
    return unique_lowercase_words - stopwords

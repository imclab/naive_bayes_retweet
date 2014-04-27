# -*- coding: utf-8 -*-
import math
import operator
import re
import sys
import tweepy
import yaml

# It may be worth having api keys stored in YAML file as well (if it's worth..)
auth = tweepy.OAuthHandler('consumer_key', 'consumer_secret')
auth.set_access_token('access_token', 'access_token_secret')
api = tweepy.API(auth)

class NaiveBayes:
    def __init__(self, yaml_file):
        # open YAML file
        self.data = yaml.load(open("data.yaml").read())

    def train(self, true_file, false_file):
        self.data["true_category_count"]  = 0
        self.data["false_category_count"] = 0
        self.data["true_category_word_count"]  = 0
        self.data["false_category_word_count"] = 0
        self.data["true_words"] = {}
        self.data["false_words"] = {}

        true_data = open(true_file, "r")
        for row in true_data:
            # ID  TWEET
            row.rstrip()
            segments = re.split('\t', row)
            tweet_id = segments[0]
            line = segments[1]
            # This is to accept only the ASCII and ja-JP chars..
            line = re.sub(u'[^\U00000030-\U0000007F\U00003000-\U0001F000]', '', segments[1].decode("utf-8"))
            # This is to surppress white space in the message (for the training purpose)
            line = re.sub(' ', '', line)
            tokens = list(line)
            # Following is the actual training part..
            self.data["true_category_count"] += 1
            for token in tokens:
                self.data["true_category_word_count"] += 1
                try:
                    self.data["true_words"][token] += 1
                except KeyError :
                    self.data["true_words"][token] = 1
        true_data.close()

        false_data = open(false_file, "r")
        for row in false_data:
            # ID  TWEET
            row.rstrip()
            segments = re.split('\t', row)
            tweet_id = segments[0]
            line = segments[1]
            # This is to accept only the ASCII and ja-JP chars..
            line = re.sub(u'[^\U00000030-\U0000007F\U00003000-\U0001F000]', '', segments[1].decode("utf-8"))
            line = re.sub(' ', '', line)
            tokens = list(line)
            self.data["false_category_count"] += 1
            for token in tokens:
                self.data["false_category_word_count"] += 1
                try:
                    self.data["false_words"][token] += 1
                except KeyError :
                    self.data["false_words"][token] = 1
        false_data.close()

    def predicted_score(self, tweet_in_question):
        # In order to predict only the likelihood score, you don't need false category. I'm including this just for fun..
        tweet_in_question = re.sub('[\r\n]', '', tweet_in_question)
        tweet_in_question = re.sub(u'[^\U00000030-\U0000007F\U00003000-\U0001F000]', '', tweet_in_question.decode("utf-8"))
        tweet_in_question = re.sub(' ', '', tweet_in_question)
        tokens = list(tweet_in_question)
        all_category_count = self.data["false_category_count"] + self.data["true_category_count"]
        score_true  = math.log(float(self.data["true_category_count"])  / float(all_category_count)) # P(category_true)
        score_false = math.log(float(self.data["false_category_count"]) / float(all_category_count)) # P(category_false)
        for token in tokens:
            try:
                score_true +=  math.log(float(self.data["true_words"][token])  / float(self.data["true_category_word_count"]))
            except KeyError:
                pass
            try:
                score_false += math.log(float(self.data["false_words"][token]) / float(self.data["false_category_word_count"]))
            except KeyError:
                pass
        return score_true


    def write_yaml(self):
        yaml_file = "data.yaml"
        stream = file(yaml_file, 'w')
        yaml.dump(self.data, stream, encoding=("utf-8"), allow_unicode=True)



def main(yaml_file, tweet_file, tweeted_file):
    bayes = NaiveBayes(yaml_file)
    # Following lines should be used only for (re-)training the model and store it to YAML file
    #bayes.train("train_ja/violin.true", "train_ja/violin.false")
    #bayes.write_yaml()

    tweeted_set = {}
    tweeted_data = open(tweeted_file, "r")
    for i in tweeted_data:
        i = re.sub('[\r\n]', '', i)
        tweeted_set[i] = 1
    tweeted_data.close()

    tweet_list = []
    tweet_data = open(tweet_file, "r")
    for row in tweet_data:
        row.rstrip()
        segments = re.split('\t', row)
        tweet = segments[1]
        tweet.rstrip()
        tweet_id = segments[0]
        tweet_list.append([bayes.predicted_score(tweet), tweet_id, tweet])
    tweet_list.sort(key = operator.itemgetter(0), reverse=True)
    tweet_data.close()
    for i in tweet_list:
        print str(i[0]) + "\t" + i[1] + " " + i[2],
        i[2] = re.sub('[\r\n]', '', i[2])
        if (i[2] in tweeted_set):
            # This tweet has already been RTed, so should be skipped
            continue
        # Write the retweeted value to the file and retweet
        tweeted_data = open(tweeted_file, 'a')
        tweeted_data.write(i[2])
        tweeted_data.write('\n')
        tweeted_data.close()
        print "Retweet: " + i[1] + " " + i[2]
        api.retweet(i[1])
        break


if __name__ == '__main__':
    args = sys.argv
    if len(args) != 4:
        sys.stderr.write("Usage: python " + args[0] + "YAML_file Tweet_file Tweeted_file\n")
        sys.exit()

    main(args[1], args[2], args[3])

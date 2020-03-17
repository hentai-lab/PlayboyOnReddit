# -*- coding: utf-8 -*-
from helpers import read_json

import logging
import time
import praw
import os


class Bot:
    def __init__(self):
        self.credentials = read_json('settings.json')
        self.logging_('%(levelname)s: %(asctime)s - %(message)s')

        self.reddit = self.authenticate()

    @staticmethod
    def logging_(logging_format):
        logging.basicConfig(level=logging.INFO, format=logging_format)

    def authenticate(self):
        logging.info("Authenticating...")
        reddit = praw.Reddit(
            user_agent=self.credentials.get('USER_AGENT'),
            client_id=self.credentials.get('CLIENT_ID'),
            client_secret=self.credentials.get('CLIENT_SECRET'),
            username=self.credentials.get('USERNAME'),
            password=self.credentials.get('PASSWORD')
        )

        logging.info("Authenticated as {}".format(reddit.user.me()))

        return reddit

    def process_submission(self, submission):
        title = submission.title
        url = submission.url
        x_post = "[r/{}] ".format(submission.subreddit.display_name)
        source_url = 'https://www.reddit.com' + submission.permalink

        new_post_title = x_post + title

        if len(new_post_title) > 293:
            new_post_title = new_post_title[0:290] + '...'

        if submission.over_18:
            new_post_title += ' | NSFW'

        new_post_url = url
        post_to = \
            self.reddit.subreddit(self.credentials.get('SUBREDDIT_TO_POST'))

        self.new_post(post_to, new_post_title, new_post_url, source_url)
        logging.info(new_post_title)

        return new_post_url, new_post_title

    @staticmethod
    def process_comment(submission, post_url, post_title):
        x_post = "[r/{}] ".format(submission.subreddit.display_name)
        playboy_on_reddit = \
            '[r/playboyonreddit](https://www.reddit.com/r/playboyonreddit)'
        sub_ = '[{}](https://www.reddit.com/r/{})'.format(
            x_post, submission.subreddit.display_name)
        post_ = '[{}]({})'.format(post_title, post_url)

        body = "reddit.\n\n    \u2022 [{}] [{}] {}.".\
            format(playboy_on_reddit, sub_, post_)

        submission.reply(body)

    def new_post(self, subreddit, title, url, source_url):
        if self.credentials.get('POST_MODE') == 'direct':
            post = subreddit.submit(title, url=url)
            comment_text = \
                "[Link to original post here]({})".format(source_url)
            post.reply(comment_text).mod.distinguish(sticky=True)
        elif self.credentials.get('POST_MODE') == 'comment':
            subreddit.submit(title, url=source_url)
        else:
            logging.ERROR('Invalid POST_MODE chosen.')

    def monitor(self, submissions_found):
        counter = 0
        for sub_reddit in self.credentials.get('SUBREDDITS_TO_MONITOR'):
            for submission in self.reddit.subreddit(sub_reddit).\
                    hot(limit=self.credentials.get('SEARCH_LIMIT')):
                if submission.id in submissions_found:
                    break
                post_url, post_title = self.process_submission(submission)
                self.process_comment(submission, post_url, post_title)
                submissions_found.append(submission.id)
                counter += 1

                with open('../data/submissions_processed.txt', 'a') as f:
                    f.write(submission.id + '\n')

                logging.info(str(counter) + ' submission(s) found')
                logging.info('Waiting...')
                time.sleep(self.credentials.get('WAIT_TIME'))

    @staticmethod
    def get_submissions_processed():
        if not os.path.isfile('../data/submissions_processed.txt'):
            submissions_processed = []
        else:
            with open('../data/submissions_processed.txt', 'r') as f:
                submissions_processed = f.read()
                submissions_processed = submissions_processed.split('\n')
        return submissions_processed

    def __call__(self, *args, **kwargs):
        logging.info('Bot running...')
        submissions_found = self.get_submissions_processed()
        while True:
            try:
                self.monitor(submissions_found)
            except Exception as e:
                logging.warning("Random exception occurred: {}".format(e))
                time.sleep(self.credentials.get('WAIT_TIME'))


if __name__ == '__main__':
    Bot().__call__()

gimport os
import time
from twython import Twython
import model

USERNAME = 'kibitzerbot'
CONSUMER_KEY = os.environ['TWITTER_CONSUMER_KEY']
CONSUMER_SECRET = os.environ['TWITTER_CONSUMER_SECRET']
OAUTH_TOKEN = os.environ['TWITTER_OAUTH_TOKEN']
OAUTH_TOKEN_SECRET = os.environ['TWITTER_OAUTH_TOKEN_SECRET']
TWEET_LENGTH = 140
TWEET_URL_LENGTH = 21

TWEET_EVERY_N_SECONDS = 60*5 # e.g. 60*10 = ten minutes between each tweet

def twitter_handle():
    return Twython(CONSUMER_KEY, CONSUMER_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET)

def submit_tweet(message, handle=None):
    if not handle:
        handle = twitter_handle()
    handle.update_status(status=message)

def extract_subject(message):
    bad_keys = ['@', '#']
    words = [word for word in message.split(' ') if all([key not in word for key in bad_keys])]
    return model.subject_from_message(' '.join(words))

def reply_to_mention(mention):
    username = mention['user']['screen_name']
    subject = extract_subject(mention['text'])
    reply = model.main(N=1, subject=subject, verbose=False, get_related=False)
    if not reply:
        return None
    return '.@{0} {1}'.format(username, reply[0])

def reply_to_mentions(handle, last_tweet_id=None):
    """
    checks for mentions since my last tweet
    for each mention:
        extracts a subject from the message,
        and replies to the user with advice on that subject
    """
    did_something = False
    for mention in handle.get_mentions_timeline(include_rts=0, since_id=last_tweet_id):
        print mention
        message = reply_to_mention(mention)
        if message is None:
            continue
        mention_id = mention['id_str']
        print message
        handle.update_status(status=message, in_reply_to_status_id=mention_id)
        did_something = True
    return did_something

def get_my_last_status(handle):
    ms = handle.get_user_timeline(screen_name=USERNAME, count=1)
    if not ms:
        return None
    return ms[0]['id_str']

def get_message(handle, subject=None):
    messages = model.main(N=1, subject=subject, verbose=False)
    assert len(messages[0])
    message = messages[0]
    assert len(message) <= TWEET_LENGTH
    return message

def main():
    handle = twitter_handle()
    while True:
        last_status_id = get_my_last_status(handle)
        did_something = reply_to_mentions(handle, last_tweet_id=last_status_id)
        if not did_something:
            message = get_message(handle)
            print message
            submit_tweet(message, handle)
        time.sleep(TWEET_EVERY_N_SECONDS)

if __name__ == '__main__':
    main()

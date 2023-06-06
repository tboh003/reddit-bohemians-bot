import praw
import requests
import logging
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import os

# initiate logger
logger = logging.getLogger(__name__)
logging.basicConfig(format="%(asctime)s %(levelname)s - %(message)s")
logger.setLevel(logging.DEBUG)

# params
url = 'https://www.bohemians.cz'
datetime_format = '%Y-%m-%dT%H:%M:%S'
subreddit_name = 'r/BohemiansPraha'
client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')
username = os.getenv('USERNAME')
password = os.getenv('PASSWORD')
user_agent = os.getenv('USER_AGENT') or "python:bohemka-bot:v0.1 (by u/tomiob)"
noop = os.getenv('NOOP') or False


def retrieve_webpage(url: str) -> BeautifulSoup:
    logger.info(f'retrieving page {url}')
    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")
    return soup


def parse_webpage_data(soup: BeautifulSoup) -> dict:
    articles = {}
    logger.info('looking for new articles')
    articles_tags = soup.find_all('article', class_='article')
    for article_tag in articles_tags:
        title = article_tag.find('h2').text.strip()        
        date = datetime.strptime(article_tag.find('time')['datetime'], datetime_format)
        link = f'{url}{article_tag.parent["href"]}'
        logger.info(f'found article:\ntitle: {title}\ndate: {date}\nlink :{link}\n')
        articles[link] = {"title": title, "date": date, "link": link}
        logger.debug(articles[link])
    return articles


def find_new_articles(articles: dict) -> dict:
    new_articles = []    
    time_baseline = datetime.now() - timedelta(hours=2)
    logger.info(f'looking for latest article published after time baseline: {time_baseline}')

    for article in articles.values():
        if article['date'] > time_baseline:
            logger.info(f'new article: {article["title"]}')
            new_articles.append(article)
    return new_articles


def post_to_subreddit(title: str, url: str):
    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        password=password,
        user_agent=user_agent,
        username=username
    )
    subreddit = reddit.subreddit(subreddit_name)
    return subreddit.submit(title=title, url=url)


if __name__ == "__main__":
    webpage = retrieve_webpage(url)
    articles = parse_webpage_data(webpage)
    new_articles = find_new_articles(articles)
    logger.debug(f'new articles:\n{new_articles}')

    for article in new_articles:
        logger.info(f'posting article {article["title"]} to subreddit {subreddit_name}')
        if noop:
            logger.info('noop parameter is True, not posting')
        else:
            submission = post_to_subreddit(title=article['title'], url=article['link'])
            logger.debug(f'submission created: {submission.created_utc}')

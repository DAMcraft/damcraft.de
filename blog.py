import hashlib
import os
import base64
from datetime import datetime
from functools import cache

import markdown

blog_directory = 'blog_posts'


class BlogPost:
    def __init__(self, title: str, summary: str, date: str, image: str, content: str, url_name: str = None):
        self.title = title
        self.url_name = url_name or title.lower().replace(" ", "-")
        self.summary = summary
        self.date = date
        self.image = image or None
        self.content = markdown.markdown(content)

    @property
    @cache
    def hash(self):
        digest = hashlib.md5(self.url_name.encode()).hexdigest()
        base64_hash = base64.b64encode(digest.encode()).decode()
        truncated_hash = base64_hash[:4]  # 64 ^ 4 = 16,777,216 possible hashes, should be enough
        return truncated_hash

    def __repr__(self):
        return f'<BlogPost title="{self.title}" date="{self.date}" url_name="{self.url_name}">'


def get_blog_posts():
    blog_posts = []
    for filename in os.listdir(blog_directory):
        with open(os.path.join(blog_directory, filename), encoding='utf-8') as f:
            title = f.readline().strip()
            url_name = filename.split('.')[0]
            summary = f.readline().strip()
            date = f.readline().strip()
            image = f.readline().strip()
            f.readline()  # skip the empty line
            content = f.read()
            blog_posts.append(BlogPost(title, summary, date, image, content, url_name))
    blog_posts.sort(key=lambda x: x.date, reverse=True)
    return blog_posts


@cache
def get_rss():
    posts = ""
    for post in get_blog_posts():
        blog_img = ''
        if post.image:
            blog_img = f'<img src="https://damcraft.de{post.image}" alt="{post.title}" style="max-width: 100%;">'
        rss_content = f"""
            <h2>{post.title}</h2>
            <p><i>{post.summary}</i></p>
            {blog_img}
            {post.content}
        """.replace("]", "&#93;").replace("[", "&#91;")
        posts += f"""<item>
            <title>{post.title}</title>
            <link>https://damcraft.de/blog/{post.url_name}</link>
            <description><![CDATA[{rss_content}]]></description>
            <pubDate>{datetime.strptime(post.date, "%Y-%m-%d").strftime("%a, %d %b %Y %H:%M:%S %z")}</pubDate>
            <guid isPermaLink="true">https://damcraft.de/blog/{post.url_name}</guid>
        </item>"""
    data = f"""<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
    <channel>
        <title>dam's blog</title>
        <link>https://damcraft.de</link>
        <description>My little place to ramble and rant on the internet</description>
        {posts}
    </channel>
    </rss>"""
    return data


if __name__ == '__main__':
    for blog_post in get_blog_posts():
        print(blog_post)
        print(blog_post.content)
        print(blog_post.hash)

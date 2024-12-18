import hashlib
import os
import base64
from datetime import datetime
from functools import cache
import pytz
import markdown

blog_directory = 'blog_posts'


class BlogPost:
    def __init__(
            self,
            title: str,
            summary: str,
            date: str,
            content: str,
            url_name: str = None,
            blog_hash: str = None,
            image: str = None
    ):
        if not title or not summary or not date or not content:
            raise ValueError("Missing required fields")
        self.title = title
        self.url_name = url_name or title.lower().replace(" ", "-")
        self.summary = summary
        self.date = date
        self.image = image
        self.hash = blog_hash or self._get_hash()
        self.content = markdown.markdown(content, extensions=['fenced_code', 'codehilite', 'extra'])

    def _get_hash(self):
        digest = hashlib.md5(self.url_name.encode()).hexdigest()
        base64_hash = base64.b64encode(digest.encode()).decode()
        truncated_hash = base64_hash[:4]  # 64 ^ 4 = 16,777,216 possible hashes, should be enough
        return truncated_hash

    def __repr__(self):
        return f'<BlogPost title="{self.title}" date="{self.date}" url_name="{self.url_name}">'


def get_blog_posts():
    blog_posts = []
    for filename in os.listdir(blog_directory):
        with open(os.path.join(blog_directory, filename), encoding='utf-8', errors='ignore') as f:
            url_name = filename.split('.')[0]

            data = {
                "title": "",
                "summary": "",
                "date": "",
                "content": "",
                "image": None,
                "hash": None,
                "url_name": url_name
            }

            done = False
            while not done:
                line = f.readline().strip()
                if line.replace("-", "").strip() == "":
                    done = True
                else:
                    try:
                        key, value = line.split(":", 1)
                    except ValueError:
                        raise ValueError(f"Invalid line: {line}")
                    key = key.strip().lower()
                    if key not in data:
                        raise ValueError(f"Unknown key: {key}")
                    data[key] = value.strip()

            data["content"] = f.read()
            data["blog_hash"] = data["hash"]
            del data["hash"]
            blog_posts.append(BlogPost(**data))

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
            <pubDate>{datetime.strptime(post.date, "%Y-%m-%d").astimezone(pytz.timezone("UTC")).strftime("%a, %d %b %Y %H:%M:%S %z")}</pubDate>
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

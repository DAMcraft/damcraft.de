import hashlib
import json
import os
import base64
from datetime import datetime
from multiprocessing import Lock

import pytz
import markdown

import helpers

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

        if not os.path.exists(self._get_comments_directory()):
            os.makedirs(self._get_comments_directory())

        self._comments_lock = Lock()
        self._cached_comments: [Comment] or None = None
        self._comments_needs_update = True

    def _get_comments_directory(self):
        return os.path.join(blog_directory, 'comments', self.url_name)

    def _get_hash(self):
        digest = hashlib.md5(self.url_name.encode()).hexdigest()
        base64_hash = base64.b64encode(digest.encode()).decode()
        truncated_hash = base64_hash[:4]  # 64 ^ 4 = 16,777,216 possible hashes, should be enough
        return truncated_hash

    def mark_comments_for_update(self):
        with self._comments_lock:
            self._comments_needs_update = True

    def _load_comments_from_disk(self):
        directory = self._get_comments_directory()
        comments = []

        for filename in os.listdir(directory):
            if not filename.endswith('.json') or not os.path.isfile(os.path.join(directory, filename)):
                continue

            with open(os.path.join(directory, filename), encoding='utf-8', errors='ignore') as f:
                try:
                    data = json.load(f)
                    comment_id = int(filename.split('.')[0])
                    comment = Comment(**data, comment_id=comment_id)
                    comments.append(comment)
                except (json.JSONDecodeError, TypeError) as e:
                    print(f"Error loading comment from {filename}: {e}")
                    continue

        comments.sort(key=lambda x: x.timestamp)
        return comments

    def get_comments(self):
        with self._comments_lock:
            if self._comments_needs_update:
                self._cached_comments = self._load_comments_from_disk()
                self._comments_needs_update = False
        return self._cached_comments

    def add_comment(self, user_name: str, user_id: int, comment: str, timestamp: int):
        with self._comments_lock:
            comment_id = 0
            directory = self._get_comments_directory()
            for filename in os.listdir(directory):
                if not filename.endswith('.json') or not os.path.isfile(os.path.join(directory, filename)):
                    continue
                comment_id = max(comment_id, int(filename.split('.')[0]))

            comment_id += 1
            with open(os.path.join(directory, f'{comment_id}.json'), 'w', encoding='utf-8') as f:
                data = {
                    'user_name': user_name,
                    'user_id': user_id,
                    'comment': comment,
                    'timestamp': timestamp
                }
                f.write(json.dumps(data, indent=4))

        self.mark_comments_for_update()

    def edit_comment(self, comment_id: int, new_content: str):
        directory = self._get_comments_directory()
        file_path = os.path.join(directory, f'{comment_id}.json')

        if not os.path.exists(file_path):
            return False

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        data['comment'] = new_content
        data['edited_timestamp'] = int(datetime.now().timestamp())

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(data, indent=4))

        self.mark_comments_for_update()
        return True

    def delete_comment(self, comment_id: int):
        directory = self._get_comments_directory()
        file_path = os.path.join(directory, f'{comment_id}.json')

        if not os.path.exists(file_path):
            return False

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        data['is_deleted'] = True

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(data, indent=4))

        self.mark_comments_for_update()
        return True

    def __repr__(self):
        return f'<BlogPost title="{self.title}" date="{self.date}" url_name="{self.url_name}">'


class Comment:
    def __init__(
            self,
            comment_id: int,
            user_name: str,
            user_id: int,
            comment: str,
            timestamp: int,
            edited_timestamp: int = None,
            is_deleted: bool = False
    ):
        self.comment_id = comment_id
        self.user_name = user_name
        self.user_id = user_id
        self.timestamp = timestamp
        self.edited_timestamp = edited_timestamp
        self.is_deleted = is_deleted
        self.date_str = helpers.timestamp_to_relative(timestamp)
        self.edited_date_str = helpers.timestamp_to_relative(edited_timestamp) if edited_timestamp else None

        if is_deleted:
            self.comment = "<span class='deleted-comment'>[deleted]</span>"
            self.edited_timestamp = None
            self.edited_date_str = None
        else:
            self.comment = (
                comment.replace("&", "&amp;")
                .replace(">", "&gt;")
                .replace("<", "&lt;")
                .replace("'", "&#39;")
                .replace('"', "&#34;")
                .replace("\n", "<br>")
            )

    def get_edited_date_string(self):
        if not self.edited_timestamp:
            return None
        date = datetime.fromtimestamp(self.edited_timestamp)
        return date.strftime("%Y-%m-%d %H:%M")


def get_blog_posts():
    blog_posts = []
    for filename in os.listdir(blog_directory):
        if not filename.endswith('.md') or not os.path.isfile(os.path.join(blog_directory, filename)):
            continue
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


def get_rss(blog_posts):
    posts = ""
    for post in blog_posts:
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

import hashlib
import html
import json
import os
import base64
import time
from datetime import datetime
from multiprocessing import Lock

import markdown
import bs4

import helpers
from comment_auth import get_user_data_from_request

blog_directory = 'blog_posts'


class BlogPost:
    def __init__(
            self,
            title: str,
            summary: str,
            date: str,
            content: str,
            url_name: str = None,
            hash: str = None,  # noqa
            image: str = None,
            co_authors: str = None,
            language: str = "en",
            original_url: str = None,
    ):
        if not title or not summary or not date or not content:
            raise ValueError("Missing required fields")
        self.title = title
        self.url_name = url_name or title.lower().replace(" ", "-")
        self.summary = summary
        self.date = date
        self.image = image
        self.hash = hash or self._get_hash()
        self._content_md = content
        self.content = self._render_markdown()
        self.language = language
        self.original_url = original_url
        self.original: BlogPost | None = None  # to be set later
        if not original_url:
            self.languages = {self.language: self.url_name}
        if co_authors:
            self.co_authors = [markdown.markdown(author.strip()) for author in co_authors.split(",")]

        if not os.path.exists(self._get_comments_directory()):
            os.makedirs(self._get_comments_directory())

        self._comments_lock = Lock()
        self._cached_comments: [Comment] or None = None
        self._comments_needs_update = True

    def add_language(self, language: str, url_name: str):
        if self.original:
            raise ValueError("cannot add languages to a translated post")
        self.languages[language] = url_name

    def get_languages(self):
        if self.original:
            return self.original.get_languages()
        return self.languages

    def _render_markdown(self):
        content_html = markdown.markdown(self._content_md, extensions=['fenced_code', 'codehilite', 'extra'])
        soup = bs4.BeautifulSoup(content_html, 'html.parser')

        for img in soup.find_all('img'):
            # skip images that have the 'no-open' class
            if 'no-open' in img.get('class', []):
                continue
                
            src = img.get('src')
            if src is None:
                continue

            a_wrapper = soup.new_tag('a',
                                     href=src,
                                     target='_blank',
                                     style='cursor: zoom-in;')
            img.wrap(a_wrapper)

        return str(soup)

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
        comment_map: {int: Comment} = {}

        for filename in os.listdir(directory):
            if not filename.endswith('.json') or not os.path.isfile(os.path.join(directory, filename)):
                continue

            with open(os.path.join(directory, filename), encoding='utf-8', errors='ignore') as f:
                try:
                    data = json.load(f)
                    comment_id = int(filename.split('.')[0])
                    comment = Comment(**data, comment_id=comment_id)
                    comment_map[comment_id] = comment
                except (json.JSONDecodeError, TypeError) as e:
                    print(f"Error loading comment from {filename}: {e}")
                    continue

        for comment in comment_map.values():
            if comment.replies_to_id:
                comment.replies_to = comment_map.get(comment.replies_to_id)

        comments = list(comment_map.values())
        comments.sort(key=lambda x: x.timestamp)
        return comments

    def get_comments(self):
        with self._comments_lock:
            if self._comments_needs_update:
                self._cached_comments = self._load_comments_from_disk()
                self._comments_needs_update = False
        return self._cached_comments

    def get_comment(self, comment_id: int):
        comments = self.get_comments()
        return next((c for c in comments if c.comment_id == comment_id), None)

    def add_comment(self,
                    user_name: str, user_id: int, comment: str, replies_to: int = None,
                    platform: str = None, profile_picture: str = None, profile_url: str = None):
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
                    'timestamp': time.time(),
                    'replies_to_id': replies_to,
                    'platform': platform,
                    'profile_picture': profile_picture,
                    'profile_url': profile_url,
                }
                f.write(json.dumps(data, indent=4))

        self.mark_comments_for_update()
        return comment_id

    def _modify_comment(self, comment_id: int, update_func):
        comment_path = os.path.join(self._get_comments_directory(), f'{comment_id}.json')
        if not os.path.exists(comment_path):
            return False
        with open(comment_path, 'r+', encoding='utf-8') as f:
            data = json.load(f)
            update_func(data)
            f.seek(0)
            f.write(json.dumps(data, indent=4))
            f.truncate()

        self.mark_comments_for_update()
        return True

    def edit_comment(self, comment_id: int, new_content: str):
        def update_func(data):
            data['comment'] = new_content
            data['edited_timestamp'] = int(time.time())

        return self._modify_comment(comment_id, update_func)

    def delete_comment(self, comment_id: int):
        def update_func(data):
            data['is_deleted'] = True
            data['comment'] = ""
            data['edited_timestamp'] = int(time.time())

        return self._modify_comment(comment_id, update_func)

    def __repr__(self):
        return f'<BlogPost title="{self.title}" date="{self.date}" url_name="{self.url_name}">'


class Comment:
    def __init__(
            self,
            comment_id: int,
            user_name: str,
            user_id: int,
            platform: str,
            profile_picture: str,
            comment: str,
            timestamp: int,
            profile_url: str = None,
            edited_timestamp: int = None,
            is_deleted: bool = False,
            replies_to_id: int = None
    ):
        self.comment_id = comment_id
        self.user_name = user_name
        self.user_id = user_id
        self.platform = platform
        self.profile_picture = profile_picture
        self.timestamp = timestamp
        self.edited_timestamp = edited_timestamp
        self.is_deleted = is_deleted
        self.replies_to_id = replies_to_id
        self.profile_url = profile_url
        self.replies_to = None
        self._process_comment(comment)

    def _process_comment(self, comment):
        if self.is_deleted:
            self.comment = "<span class='deleted-comment'>[deleted]</span>"
            self.edited_timestamp = None
        else:
            self.comment = html.escape(comment).replace("\n", "<br>")

        short_comment = html.escape(comment).replace("\n", " ")
        if len(short_comment) > 100:
            short_comment = short_comment[:100] + "..."
        self.short_comment = short_comment

    @property
    def date_str(self):
        return helpers.timestamp_to_relative(self.timestamp)

    @property
    def edited_date_str(self):
        if not self.edited_timestamp:
            return None
        return helpers.timestamp_to_relative(self.edited_timestamp)


class BlogPostList(list):
    def __init__(self, *args: [BlogPost]):
        if not all(isinstance(blog, BlogPost) for blog in args):
            raise ValueError("not a BlogPost")
        sorted_blogs = sorted(args, key=lambda x: x.date, reverse=True)
        super().__init__(sorted_blogs)
        self.languages: [str] = [*{blog.language for blog in self}]
        # sort by amount of posts in each language
        self.languages.sort(key=lambda x: len([blog for blog in self if blog.language == x]), reverse=True)

        self.url_name_map: {str: BlogPost} = {blog.url_name: blog for blog in self}
        self.hash_map: {str: BlogPost} = {blog.hash: blog for blog in self}

    def get_by_language(self, language: str) -> [BlogPost]:
        return [blog for blog in self if blog.language == language]

    def get_by_url_name(self, url_name: str) -> BlogPost:
        return self.url_name_map.get(url_name)

    def get_by_hash(self, hash_: str) -> BlogPost:
        return self.hash_map.get(hash_)

    def append(self, blog_post):
        if not isinstance(blog_post, BlogPost):
            raise ValueError("not a BlogPost")
        super().append(blog_post)
        self.languages.append(blog_post.language)
        self.languages = list(set(self.languages))
        self.languages.sort(key=lambda x: len([blog for blog in self if blog.language == x]), reverse=True)
        self.url_name_map[blog_post.url_name] = blog_post
        self.hash_map[blog_post.hash] = blog_post
        self.sort(key=lambda x: x.date, reverse=True)


def get_blog_posts():
    blog_posts = BlogPostList()
    for entry in *os.scandir(blog_directory), *os.scandir(os.path.join(blog_directory, 'translations')):
        if not entry.name.endswith('.md') or not entry.is_file():
            continue
        with open(entry.path, encoding='utf-8', errors='ignore') as f:
            url_name = os.path.splitext(entry.name)[0]

            metadata = {}

            in_metadata = True
            while in_metadata:
                line = f.readline().strip()
                if line.replace("-", "").strip() == "":
                    in_metadata = False
                else:
                    try:
                        key, value = line.split(":", 1)
                    except ValueError:
                        raise ValueError(f"Invalid line: {line}")
                    key = key.strip().lower().replace(" ", "_").replace("-", "_")
                    value = value.strip()
                    metadata[key] = value

            metadata["content"] = f.read()
            metadata["url_name"] = url_name
            blog_post = BlogPost(**metadata)
            if blog_post.original_url:
                original = blog_posts.get_by_url_name(blog_post.original_url)
                assert original
                blog_post.original = original
                original.add_language(blog_post.language, blog_post.url_name)
            blog_posts.append(blog_post)

    return blog_posts


def handle_comment(blog_id, request_, blogs):
    blog: BlogPost = next((b for b in blogs if b.url_name == blog_id), None)
    if not blog:
        return
    user_data = get_user_data_from_request(request_)
    if not user_data:
        return

    content = request_.form.get("comment")
    content = helpers.sanitize_comment(content)
    if not content:
        return

    replies_to = request_.form.get("replies_to")

    comment_id = blog.add_comment(
        user_name=user_data.user_name,
        user_id=user_data.user_id,
        comment=content,
        platform=user_data.platform,
        profile_picture=user_data.profile_picture,
        profile_url=user_data.profile_url,
        replies_to=int(replies_to) if replies_to else None
    )
    return comment_id


def modify_comment(blog_id, comment_id, request_, blogs: [BlogPost]):
    comment_id = int(comment_id)
    user_data = get_user_data_from_request(request_)
    if not user_data:
        return

    blog: BlogPost = next((b for b in blogs if b.url_name == blog_id), None)
    if not blog:
        return
    comment = blog.get_comment(comment_id)
    if not comment or comment.is_deleted or comment.user_id != user_data.user_id:
        return

    action = request_.form.get('action')
    if action == 'edit':
        new_content = helpers.sanitize_comment(request_.form.get('content'))
        if not new_content:
            return
        if comment.comment == new_content:
            return  # No changes

        if not blog.edit_comment(comment_id, new_content):
            return  # Error

    elif action == 'delete':
        if not blog.delete_comment(comment_id):
            return
    else:
        return

    blog.mark_comments_for_update()


def get_rss(blog_posts: [BlogPost], language):
    items = []
    for post in blog_posts:
        if post.language not in (language, "en"):
            continue
        pub_date = datetime.strptime(post.date, "%Y-%m-%d").strftime("%a, %d %b %Y 00:00:00 +0000")
        description = f"""
            <h2>{html.escape(post.title)}</h2>
            <p><i>{html.escape(post.summary)}</i></p>
            {f'<img src="https://lina.sh{post.image}" alt="{html.escape(post.title)}">' if post.image else ''}
            {post.content}
        """.replace("[", "&#91;").replace("]", "&#93;")

        item = f"""
        <item>
            <title>{post.title}</title>
            <link>https://lina.sh/blog/{post.url_name}</link>
            <guid isPermaLink="true">https://lina.sh/blog/{post.url_name}</guid>
            <pubDate>{pub_date}</pubDate>
            <description><![CDATA[
                {description}
            ]]></description>
        </item>
        """
        items.append(item)
    data = f"""<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
    <channel>
        <title>lina's blog</title>
        <link>https://lina.sh</link>
        <description>My little place to ramble and rant on the internet</description>
        {"".join(items)}
    </channel>
    </rss>"""
    return data


def get_news_sitemap(blog_posts: [BlogPost]):
    urls = []
    for post in blog_posts:
        pub_date = post.date

        url = f"""
        <url>
            <loc>https://lina.sh/blog/{post.url_name}</loc>
            <news:news>
                <news:publication>
                    <news:name>lina's blog</news:name>
                    <news:language>{post.language}</news:language>
                </news:publication>
                <news:publication_date>{pub_date}</news:publication_date>
                <news:title>{html.escape(post.title)}</news:title>
            </news:news>
        </url>
        """
        urls.append(url)

    sitemap_data = f"""<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
            xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">
        {''.join(urls)}
    </urlset>"""

    return sitemap_data


if __name__ == '__main__':
    for blog_post_ in get_blog_posts():
        print(blog_post_)
        print(blog_post_.content)
        print(blog_post_.hash)

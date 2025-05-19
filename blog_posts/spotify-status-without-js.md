Title: Fully automatic updating Spotify status... without JavaScript?
Summary: How I managed to keep my website JavaScript-free while still showing my current Spotify status in real-time.
Date: 2024-12-08
Image: /assets/blog/spotify-status.png
Hash: spotify
---------
## The challenge

Typically, when you want real-time updates (like displaying the song you're listening to on Spotify), 
you'd use JavaScript. It makes sense - JavaScript is the go-to for dynamic content. 
But well, my website *was* written fully without JavaScript, and I didn't want to just "throw that away" for adding a Spotify status.
I wanted to **avoid JavaScript** completely and still keep the status updated **automatically and dynamically**.

So how did I do it? Here's the trick: 
I used server-side streaming and some clever use of CSS. No fancy JavaScript, just good old HTML and CSS (and a bit of Python magic).

## How it works
The basic idea is pretty simple:  
The connection that fetches the HTML is kept open. This allows the server to "append" new data at the end of the HTML file.  
I can now send `<style>` tags every time the status changes, these tags contain the new spotify status and overwrite the old one.  

## No JavaScript, just HTML and CSS in the frontend
Instead of changing the actual HTML structure or DOM (which is what JavaScript would normally do), I simply update the CSS. 
Yep, all the dynamic changes - like song title, progress, album art - are handled by changing the styles.

Here's how I do it:
<ul>
    <li> I create a skeleton HTML page that contains placeholders for things like the song title and album art.</li>
    <li> I keep the connection open between the server and the browser using something called server-sent events (essentially, a live stream of data from the server to the browser).</li>
    <li> When there’s an update (song change, playback status, etc.), I inject new CSS into the page. This CSS is what updates things like the song title and progress bar.</li>
</ul>

This idea was suggested to me by my friend yui ([https://zptr.cc/](https://zptr.cc/)), 
whose website is genuinely amazing, please check it out!

### Example: Injecting CSS for a song update
When the server detects that a song has changed, instead of manipulating the DOM, I send the new song title as a CSS rule. It might look like this:
```html
<style>
  .song-title::before {
    content: "New Song Title";
  }
</style>
```
This CSS rule gets appended at the bottom of the page and updates the `.song-title` element with the new song title. 
And because CSS is cascading (the last rule "wins"), it overrides the old song title.
For song progress, I use CSS animations to move the progress bar forward, which runs based on the current playback position.

## Syncing everything
Now, one issue with CSS animations is that they’re not always perfectly synced to real-time events. 
So to make sure everything is accurate, I send a full update (with fresh CSS) every few seconds. 
That way, if something is off, like the song is paused or the progress bar is wrong, the page automatically corrects itself.
Every five seconds, the server sends a full update with the current song, progress, and album art. 
If something changes in the meantime, if I for example pause the song, skip to the next one, or change the timestamp, the **server sends an update immediately**.
<video src="/assets/blog/spotify-playing.mp4" autoplay loop muted></video>

## The code behind it
Instead of using JavaScript to make API requests and update the DOM, the server periodically checks Spotify for the latest status (song title, artist, playback position) and then sends updates via an open connection to the browser. It might look something like this (simplified):

1. The server listens for events (like song changes or playback updates). 
2. When something changes, it generates new CSS based on the current status. 
3. It sends this CSS to the browser in real-time via the open connection.

With Flask (a python-webserver, this is what use for my backend), this is actually quite simple!  
I just write a python generator that yields the CSS updates, and Flask takes care of the rest.
```python
while True:
    event = event_queue.get()
    if event is None:
        break
    yield event
```
Here, `event_queue.get()` is waiting for new events to come in.
Now I can just add anything I want to the `event_queue` and it will be sent to the browser in real-time!

## Why does this work?
Here’s the cool part: the server doesn’t need to manipulate the actual content on the page. 
It only sends updated CSS, and since CSS can control a lot of things (like content, animations, and even visibility), it’s all I need to keep the page updated.

By keeping the server connection open and continuously sending updates (in the form of CSS), I get the same real-time effect you’d get with JavaScript, but without ever touching JS. 
It's essentially "live-updating" without the need for client-side code. Pretty neat, huh?

## Problems 
Of course, this approach isn't perfect.
For example, if the connection is kept open, the browser will show the page as "loading" until the connection is closed.
I solved this by embedding the status in an iframe (which was lazy loaded) and only "teleporting" the status to the main page after 5 seconds,
which is enough time for the website to load. Since the website can't fall back to a loading state,
the browser will display it as fully loaded, despite some elements *still* loading in the background.
To "close" the spotify status I had to add a button on the *main* page which overlays the iframe, this toggles a checkbox which is used to hide the iframe.

## Conclusion
It's a fun little experiment that shows how you can achieve real-time updates without JavaScript.
Yes, it would've been way easier with JavaScript, and I spent way too many hours on this, *but* it was incredibly fun to figure out!  
    
The code for this can be found on my GitHub:
[https://github.com/DAMcraft/damcraft.de](https://github.com/DAMcraft/damcraft.de)

<div class="listening-wrapper">
    <iframe loading="lazy" class="listening-to" src="/listening_to"></iframe>
</div>

<style>
.listening-to {
    border: none;
    background: none;
    width: 350px;
    height: 140px;
}
.listening-wrapper {
    margin-top: 20px;
    vertical-align: middle;
    display: flex;
    justify-content: center;
}
</style>
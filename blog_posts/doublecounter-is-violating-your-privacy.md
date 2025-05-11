Title: DoubleCounter is a glorified doxing tool.
Summary: How DoubleCounter brutally violates the privacy rights of over 40 million users — while making nearly half a million USD in revenue (2022).
Date: 2025-05-11
Image: /assets/blog/doxing-users.png
Hash: dcounter
---------
<div class="subtext">This is a satirical modification of the DoubleCounter logo. Original logo owned by Tellter SAS.</div>  

### TL;DR
DoubleCounter sells access to your account-links and enables doxing, whilst claiming the exact opposite. Of course, without consent.
If you verified with DoubleCounter, your data was collected under misleading terms and alt account data was made available 
via tools like Doogle and Lens for potential public exposure **without** your proper consent.
If this concerns you, please go to <a href="https://dcounter.damcraft.de/" target="_blank">https://dcounter.damcraft.de/</a>.
We're collecting complaints from users to file a complaint with the French Data Protection Authority ("CNIL") against DoubleCounter.  
If you are a server owner, please consider removing DoubleCounter from your server. Discord added many raid-protection features
already, and automatically stops banned users from joining on alts if they detect it as one. Stopping very few users by
exposing the private data of all other users is not a good trade-off. On top of this, DoubleCounter detects
an incredibly high number of false positives, which users cannot even appeal against.

### What is DoubleCounter?

DoubleCounter presents itself as a "privacy-respecting"[^privacy-respecting] Discord bot designed to prevent users from
joining servers with alternate ("alt") accounts. For stopping trolls, spammers, ban evaders, etc. 
It operates on a massive scale, having "verified" over 40 million[^40m-users] users across 500,000 Discord servers[^500k-servers]. 
This verification process, just opening a link that collects some data on your browser and IP[^browser-data], 
helps them generate nearly 400,000$ USD in annual revenue[^annual-revenue] <sup>(data from 2022)</sup>
through ads placed on that verification page and selling premium features[^premium].

This "anti-fraud" system systematically seems to operate in direct conflict with user privacy and
the most fundamental rights guaranteed under the EU's General Data Protection Regulation ("GDPR"). Because
the parent company, Tellter, is based in France[^privacy-policy], **all** users are protected by the GDPR (even if they are not EU citizens)[^gdpr-3-1].  

A quick overview on two of DoubleCounter's features:  

* **Doogle**: A "search" engine. Put in a Discord user, get back a list of other Discord accounts that DoubleCounter thinks are
  alts, often based on shared IPs or browser cookies from that verification click.
  Free users get three lifetime searches; paying subscribers can use this tool as much as they want.
  
* **Lens**: A subscription service showing a user's history across different servers using DoubleCounter – things like
  bans, kicks, or other moderation actions.  

These tools have massive privacy issues, which we'll discuss in detail later.
They basically turn the private data that DoubleCounter collect into publicly searchable information, 
effectively doxing tools.


### "All data is automatically processed, encrypted, and never viewed by humans. We do not sell or share your data".
This is the promise made in the very first paragraph of their privacy policy[^privacy-policy], the policy under
which tens of millions of users clicked "verify"[^40m-users]. It's what everyone immediately saw, *if* they even bothered to read the
privacy policy.  

It is not accurate based on their actual practices:

* **Data *is* shared**: User data, specifically the links between your main account and any suspected alts (including
  Discord IDs and usernames), is routinely shared with server moderators via logs when an alt is detected trying to
  join. Critically, it's also shared (or rather, made publicly searchable) through the "Doogle"
  and "Lens" features. The massive issue with these tools will be explained in detail later.
  There is a documented case of it having sent a direct message to a user revealing the identity (username and ID) 
  of a household member flagged as an alt simply because they shared an IP
  address. This exposed a private, sensitive account owned by that housemate to someone else in their home, which lead to
  them being labeled a "creep".  

![](/assets/blog/exposing-accounts.png)
<div class="subtext">
This is a screenshot of the DM that was sent to a user, revealing the identity of a household member flagged as an alt.
After sending a friend request to the user, it was revealed that this seems to be a private 18+ account.
</div>

* **Data *is* sold**: "We do not sell [...] your data"? Access to "Doogle" search capabilities (beyond *three* free
  searches in your lifetime) and the "Lens" feature (which shows a user's moderation history across different servers) requires a
  paid subscription[^premium]. Why would charging money for access to user data not be selling user data? 

* **Data *is* viewed by humans**: The claim that data is "never viewed by humans" just fails instantly.
  Server mods see the usernames and IDs in logs. Paying users see the linked accounts of anyone via
  Doogle/Lens. And DoubleCounter's own staff clearly access and discuss this data internally, 
  as evidenced by email responses providing specific linked account IDs. All alt links and join attempts are also 
  forwarded to DoubleCounter admins, and routinely shared publicly in their Discord server.[^publicly-sharing]

![](/assets/blog/sharing-data.png)

This is a direct contradiction of the privacy policy's very first promise.

### A pattern of privacy violations

This is where we dive a bit deeper into *why* they're violating privacy laws like the GDPR, this should hopefully be easy to understand
even if you're not an expert.

#### Discord IDs are personal data. Linking two together is linking stuff to *you*.

For years, DoubleCounter claimed (in bot messages[^bot-not-pii], its privacy policy[^privacy-policy], and direct user
communications) that Discord User IDs – a string of numbers that uniquely identifies Discord accounts – are not "Personally Identifiable
Information (PII)" under the GDPR. They incorrectly used this U.S.-centric term ("PII") to justify refusing deletion
requests for linked account data, sharing this data around publicly, and whatnot – which is not how it works under the GDPR[^gdpr-4-1].

This argument fails because GDPR does not rely on the narrow concept of "PII". Under GDPR, any information that
relates to an identifiable person qualifies as personal data[^gdpr-4-1].
Connecting something to an online identity is considered personal data, even if you don't know the "real-world" identity of the person behind it.
A Discord User ID is personal data because:

- It directly identifies a specific account on Discord.
- Using Discord’s API[^discord-api-id] or public tools like [discord.id](https://discord.id), anyone can instantly
  retrieve the username, profile picture, and public connections tied to that ID.
- GDPR explicitly covers pseudonymised data (e.g., IDs) if it can be linked to a person using additional information –
  even if that information is held by third parties[^edpb-pseudonyms].

DoubleCounter's flawed reasoning hinges on claiming that linking accounts (e.g., associating two Discord IDs) does not
tie data to *you*. This is absurd:

- Discord IDs are unique identifiers tied to real accounts.
- Linking IDs creates a profile on users. Even without knowing their "real-world" identity, this profile
  *relates* to an *identifiable person* under GDPR.
- The links themselves are non-public personal data, as they reveal associations only DoubleCounter has created and
  stored.

By linking IDs, DoubleCounter processes personal data – full stop. GDPR compliance requires lawful justification (for example
consent or legitimate interest, we'll come to that in a second!) for this practice.

![](/assets/blog/attached-id.png)

After being presented with evidence, they eventually conceded the point in an email: "You're absolutely correct that
Discord User IDs are considered personal data"[^emails].

#### The problematic "legitimate interest" claim

Let's talk about "Legitimate Interest". Under GDPR, companies sometimes don't need your explicit *consent* to use your
data if they have a necessary reason (a "legitimate interest") *and* if using the data doesn't unfairly harm your
privacy rights[^gdpr-6-1-f]. It's a very fragile argument to make. Legitimate interest is a rather complex topic, 
companies can't just do anything they want and claim "legitimate interest". DoubleCounter's main argument for keeping the links between your
accounts, even after you ask for deletion, is "fraud prevention"[^privacy-policy].

But here are a few issues with that:

1. **It's not just storing, it's sharing**: "Fraud prevention" might justify internally flagging an account
   trying to join a server it was banned from, and preventing it from joining. But DoubleCounter goes further. They created Doogle and Lens, tools that
   essentially publish these private links to potentially anyone.
   How does letting random users (or paying subscribers) look up who might own what alt account prevent fraud in a
   specific server? It seems primarily to expose private information. Sharing or selling data collected like this is basically
   impossible to justify under legitimate interest. Their *new* privacy policy even tries to claim sharing via Doogle is covered by
   legitimate interest, which is just absolutely fundamentally flawed.

2. **Exposing *very* personal accounts**: As mentioned before, in their support server, I stumbled across the private 18+ account of a 
   person being exposed to their housemate via a DoubleCounter DM. This wasn't even Doogle/Lens, 
   it was the bot oversharing data based on a shared IP. 
   How can *any* balancing test conclude that the "interest" in potentially stopping one person from joining a server outweighs the actual harm and
   privacy violation of outing someone's private account to their family?!?
   Many people use alts for perfectly valid privacy reasons — separating stuff from personal life or 
   keeping sensitive interests separate from their main identity. Which is totally fine.
   DoubleCounter infringes on this need for privacy.

3. **Internal contradictions**: In an email exchange, after we pointed out that the `/privacy` command wasn't
   showing the linked accounts DoubleCounter knew it had[^emails], the explanation given was that the bot
   performing the checks doesn't have direct access to that stored link data. If the bot doing the "fraud prevention" 
   doesn't even use or need the stored links you refuse to delete, then how can it be necessary
   to keep them under legitimate interest? None of their claims make any sense.

4. **Not deleting data correctly**: GDPR gives you the right to say, "I object to you using my data for this 'legitimate
   interest' reason in my specific situation" (Article 21). The company then has to prove they have compelling
   grounds that override your privacy rights for *your specific case*. They can't just give a
   generic "muh fraud prevention!" excuse. Their Discord support server is *full* of users reporting that they
   want all their data deleted, and DoubleCounter just ignores them. DoubleCounter is required to inform users of this right[^gdpr-21-4], 
   which they didn't do.

#### Doogle & Lens: Your privacy for sale (whether you know it or not)

Let's be clear about Doogle and Lens. These aren't just background tools for mods. These are doxing tools, publishing
your sensitive data to paying subscribers.

The concerning part? DoubleCounter rolled out these features and used them with data collected before
these tools existed, meaning that the private accounts of *everyone* prior to the tools' launch were made public.
Without them ever being notified about it[^old-data]. 
I mean, their privacy policy still promises that they "do not sell or share your data" these days[^privacy-policy].
But you *could* know about it if you just dig into DoubleCounter more. But back then? Literally impossible to even guess this.
There was no notification about this data being made public, no asking for permission, they just took the data collected
before and decided to make it public.

If we were to ignore the fact that their privacy policy **doesn't** mention this correctly, let's assume they *would* inform
users correctly about this.
These tools would still only function because most users have no idea this is happening. 
If every time DoubleCounter linked your accounts, you got a clear message saying, 
"Hey, we think this alt is yours. We're adding this link to a public, searchable database that others can pay to access. 
Click HERE to immediately opt out and keep this private", how many people would *not* click opt-out? Almost everyone would want it kept
private. The business model for these features seems based on users not knowing what's happening and a lack of transparency, 
which is the *opposite* of what GDPR demands[^gdpr-12].


![](/assets/blog/poll.png)
<div class="subtext">We made a poll on a random Discord server using DoubleCounter - 85% of users would've opted out - if
they knew about it! (This poll is not representative, and made with a relatively small number of users, although it's worth noting
that only one person knew how their data was being used, and wouldn't have opted out 
(there's two votes, because the poll creator has created all the voting options))</div>[^project-renaissance]

#### A difficult process for exercising rights

Beyond these issues, the process of trying to exercise basic privacy rights is unnecessarily difficult.

* **Incomplete `/privacy` command**: Their policy says to use the `/privacy` command in a server to get a copy of
  your data sent to your email[^privacy-policy]. When we tried it, the bot replied, "There is no data about your account stored in our database"[^emails]. 
  But emails with support confirmed they did have data (the linked alt account ID)[^emails]. So, the official tool for data
  access appeared broken or intentionally incomplete. Their explanation changed, first claiming it only retrieves IP addresses
  (which they also said weren't stored for this user), then claiming the bot doesn't even know the user ID. 
  This prevented users from easily seeing what data was held.
  
* **Inconvenient access**: Why does the `/privacy` command only work inside servers where the bot was
  active[^privacy-policy]? What if the server owner disabled commands? You'd have to join DoubleCounter's
  specific support server just to access basic privacy settings. This is unnecessary, making it harder for users to control their data
  (although we got told that this is planned to be fixed after we complained).
  
* **Staff confusion and misinformation**: Dealing with support is very inconsistent. Users in the Discord server reported
  being told incorrect things by moderators, like data couldn't be corrected/modified ("this can't be
  changed"), or generally being discouraged from pursuing their rights.

While I cannot state definitively whether this is done out of bad faith or is a consequence of incompetence, the
process for users to exercise their privacy rights has been made excessively difficult. The former is a blatant violation
of the GDPR, the latter, though, puts into question whether an incompetent team should be put in charge of users' data
in the first place.
![](/assets/blog/privacy-respecting.png)
<div class="subtext">I would call this one "false advertisement".</div>

### The GDPR violation checklist
#### [Skip this section](#a-doxing-tool) if you prefer not to get into the specific legal articles
Based on DoubleCounter's practices and communications, here's a rundown of potential GDPR violations. 
This isn't fully exhaustive (the GDPR is quite massive!):

* **Article 5 (Principles relating to processing of personal data)**: Violated through lack of transparency, fairness 
  (misleading users), purpose limitation (using data collected for anti-fraud to power public search tools like
  Doogle/Lens without consent), and data minimization (collecting/retaining data like alt links that may not be strictly
  necessary for the stated purpose, especially when shared publicly).

* **Article 6 (Lawfulness of processing)**: The reliance on "legitimate interest" (6(1)(f)) appears very questionable,
  especially for sharing/selling data via Doogle/Lens and retaining links after deletion requests without a compelling,
  case-specific justification overriding user rights. The initial collection itself might lack a solid lawful basis due
  to misleading information provided at the time.

* **Article 7 (Conditions for consent)**: While they primarily claim legitimate interest, the ads on their verification
  page likely rely on consent for cookies/tracking, which seemed flawed (buggy banner). More importantly, using data for
  Doogle/Lens, a purpose different from the original collection, requires fresh, informed consent, which
  was never requested nor acquired.

* **Article 12 (Transparent information, communication and modalities for the exercise of the rights of the data
  subject)**: Repeatedly violated through unclear, inaccurate, and misleading information (claiming IDs aren't personal data,
  false statements in the privacy policy and bot messages, difficult-to-access privacy
  controls like a server-locked `/privacy` command). 

* **Article 13 & 14 (Information to be provided where personal data are collected/not collected from the data subject)**: 
  The old privacy policy was severely incomplete, missing mandatory information about user rights (like the right to
  complain to a DPA, restrict processing, object, or not be subject to automated decisions, and so much more),
  clear retention periods, ...

* **Article 15 (Right of access by the data subject)**: Violated by the `/privacy` command failing to return all stored
  data (specifically, the known linked alt account ID) despite the policy promising a full copy.

* **Article 16 (Right to rectification)**: Effectively hindered by staff initially claiming corrections (like unlinking
  wrongly associated household members) were impossible or couldn't be done, and not informing users of this
  right when inaccuracies were reported. If DoubleCounter wrongly linked two accounts, that is "the fault of the user". 
  They are no longer able to interact in servers with global detection without having to
  ask a mod in that server each time.  

* **Article 17 (Right to erasure / "Right to be forgotten")**: Violated by the blanket refusal to delete alt account
  links based on a weak legitimate interest claim, and potentially by continuing to share this data (via logs, and even 
  Doogle/Lens if you didn't opt out manually).

* **Article 25 (Data protection by design and by default)**: Arguably violated by designing systems (like Doogle/Lens
  and the oversharing DM "feature") that expose personal data by default, rather than prioritizing privacy from the
  beginning.

* **Article 32 (Security of processing)**: While they claim encryption, the practice of sending usernames/IDs basically 
  everywhere just shows not enough measures to ensure this "security".

<div id="a-doxing-tool"></div>
### A doxing tool fueled by ignorance

Let's call Doogle what it is in practice: 
A tool that facilitates doxing by exposing connections between potentially private or anonymous accounts. 
DoubleCounter might claim they're for "fraud prevention"[^privacy-policy] or "moderation", 
but the efficiency of Doogle relies almost entirely on an ethically dubious point: **most users have no idea their data is being used this way**. 
Doogle publishes sensitive information of users that they deliberately kept private, without the knowledge or consent of the users involved. 
There is a word to describe this: *doxing*.

Think about it:

1.  A user joins a server, clicks a verification link, maybe skims a privacy policy that (at the time) promised data wouldn't be shared or sold.

2.  DoubleCounter links this account to another based on IP or browser data.

3.  Later, DoubleCounter launches Doogle/Lens and populates it with these previously collected links *without telling the users* or getting new consent.

4.  Now, anyone (especially paying subscribers) can potentially look up User A and find out they also own anonymous User B.

This process bypasses **informed** consent entirely. 
The system works because users aren't aware they can (and likely would) opt out if properly informed. 
This can lead to:

* Outing anonymous accounts used for sensitive communities.

* Linking personal accounts to professional ones without a user's knowledge.

* Exposing accounts used for private hobbies or interests (like the 18+ account example).

* Allowing harassment by revealing connections someone deliberately kept separate.

They use information obtained outside Discord to do this verification — this isn't "public Discord information" 
if they get the data from outside sources. (As a matter of fact, Discord even actively tries to prevent IP leaks and fingerprinting by proxying 
literally everything through their own servers, even wiping metadata on images).
The link between those IDs is the sensitive, non-public information they are exposing and selling access to. 
It's the connection itself that users often want to keep private, and DoubleCounter built features to make those 
connections searchable, making money on the fact users aren't aware of their data being shared like this. 
This isn't "fraud prevention", it's sharing data non-consensually for profit.

![](/assets/blog/doogle-search.png)

This is still an issue with their new privacy policy! None (**!**) of the data they **ever** collected is allowed to be shared like this.
Because of this, we are pressuring DoubleCounter to delete ALL data they collected until this point, or at least ensure none
of the data is shared with anyone else anymore.  


## What can you do?

If you've ever verified with DoubleCounter, your personal data was collected under misleading terms, potentially
exposed through tools like Doogle and Lens, and made available to others **without your proper consent**. Despite these
serious privacy concerns being raised, DoubleCounter has shown little willingness to change their practices.

This is why we're gathering affected users to file a collective complaint with the French Data Protection Authority (CNIL). 
Your participation matters because data protection authorities prioritize cases affecting many users, and often
regulatory intervention is the only way to ensure compliance when companies resist voluntary changes.

**Join the complaint: <a href="https://dcounter.damcraft.de/" target="_blank">https://dcounter.damcraft.de/</a>**

The form is really easy to complete, requiring only basic information. Your
privacy matters, and by taking action today, you're helping ensure proper privacy practices 
when companies won't implement them voluntarily.

We also encourage you to file a complaint with your local Data Protection Authority or the CNIL directly if you're not in the EU.

1. **CNIL Complaint** (French only):  
   [https://www.cnil.fr/en/plaintes](https://www.cnil.fr/en/plaintes) (You can use your browser translation tool)  

2. **Local DPA** (EU only):  
   Find your local DPA here:
   [https://edpb.europa.eu/about-edpb/about-edpb/members_en](https://edpb.europa.eu/about-edpb/about-edpb/members_en)  


If you're part of a server that uses DoubleCounter, you can also let the server owner know about the issues described
here. Many server owners are not be aware of how incredibly invasive DoubleCounter's practices are, and simply want to protect
their communities. Helping them understand the full picture can make a big difference.

### Conclusion: Systematically disregarding user privacy for profit

The business model of DoubleCounter, operated by "Tellter SAS", apparently prioritizes revenue over
fundamental user privacy rights. Having a reported revenue of 400,000$ in 2022[^annual-revenue], their business model appears
heavily reliant on violating a bunch of GDPR articles.

From misleading privacy policies and inaccurate statements about data handling, to the creation of public-facing tools
like Doogle that expose private data without proper consent, their actions repeatedly disregard user's rights.
Their justification of "legitimate interest" for fraud prevention is difficult to argue with the reality of data
being widely shared, sold through subscriptions, and used in ways that can cause direct harm, such as revealing private
information.

The concept of preventing ban evasion on Discord is understandable, but the stuff that DoubleCounter does on top of that
raises so many serious ethical and legal concerns. It's so incredibly important that Tellter makes changes, including genuinely respecting
user rights, getting **informed** consent, removing privacy-invasive features like Doogle, and prioritizing user privacy
over profit. 

**None** of the data that DoubleCounter collected was *ever* allowed to be shared like this. 

We are preparing a report for the Data Protection Authority regarding DoubleCounter. If you feel your privacy rights
have been infringed in any way, please use this form to submit your information: <a href="https://dcounter.damcraft.de/" target="_blank">https://dcounter.damcraft.de/</a>.

If there is anything else, you can get in contact with me by sending an email to <a href="mailto:dcounter@damcraft.de">dcounter@damcraft.de</a> 
or contacting me on Discord (`@damcraft.de`). I also have a Discord server if you want to stay updated and chat with others about this:
<a href="https://discord.gg/mrKTxwHxv7" target="_blank">https://discord.gg/mrKTxwHxv7</a>.

## Thank you

This research took quite some time and effort. I spent way over two week on this, and I want to thank the following people for their help:  

* [tufo](https://tufo.dev)  

* [eva/kibty.town](https://kibty.town/)  

* [Patsore](http://patsore.org/)

* [nikolan](https://nikolan.net)

* [TheOnlyWayUp](https://towu.dev/)

* cd76d1d024c7276a 

* <label for="catchy-modal-toggle" class="catchy-label">Catchy</label>

* [lina](/)




## Sources
This entire post was sent to DoubleCounter to check for *any* errors. I corrected all factual errors they pointed out if they were indeed wrong, 
otherwise there will be a comment behind the source. It is important to note that DoubleCounter still insists that Discord IDs aren't PII, even
though that is completely irrelevant to the GDPR. They are personal data, and they are protected by the GDPR.

[^privacy-respecting]: They claim this themselves on their front-page: [https://doublecounter.gg/](https://web.archive.org/web/20250409172223/https://doublecounter.gg/)
[^annual-revenue]: This information is taken from the website of the parent company, Tellter. Scroll to the bottom to see that
DoubleCounter has an ARR (= Annual Recurring Revenue) of 400,000$ from DoubleCounter alone. [https://tellter.com/](https://web.archive.org/web/20250426190354/https://tellter.com/)  
Comment from DoubleCounter: 
    <i>"Your stats are correct except for the revenue, which is outdated and actually much less now. It is intentionally left as is for marketing purposes, but in fact corresponds to our best year all-time, 2022 :D
I've always liked been super transparent on everything, so if you want further details on this, you can check this Discord thread on No Text To Speech's server, where I discussed this in the past: [link](https://discord.com/channels/820745488231301210/1204592844770385971);
It even contains extracts of our cash flow statements! We currently have a bit higher revenue than in the thread, about $9000/month with still $4K to $5K in costs. After French taxes, we're quite far from the "half a million USD" headline, even though I would love for it to be real!" </i>  
We have corrected the blog post to point out this data is from 2022. We find it very misleading to put this on their website, 
and then to basically say that our stats are incorrect.
[^500k-servers]: Taken from their Discord Application Page, these numbers come officially from Discord [https://discord.com/discovery/applications/703886990948565003](https://web.archive.org/web/20250201045541/https://discord.com/discovery/applications/703886990948565003); 
As of 2024-04-28, it was in 525k servers.  

[^40m-users]: This is taken from Tellter's DoubleCounter page [https://tellter.com/portfolio/double-counter-alt-account-detection/](https://web.archive.org/web/20250426185930/https://tellter.com/portfolio/double-counter-alt-account-detection/)
[^edpb-pseudonyms]: This specific case is explained, for example, in §22 of their [Guidelines on pseudonymisation](https://www.edpb.europa.eu/system/files/2025-01/edpb_guidelines_202501_pseudonymisation_en.pdf)
[^browser-data]: This comes from their own privacy policy. Since this one is full of errors, it should be taken with a grain of salt. [https://docs.doublecounter.gg/double-counter-en/legal](https://web.archive.org/web/20250401032211/https://docs.doublecounter.gg/double-counter-en/legal)
[^premium]: They sell a Pro tier for 8.49$/month, and an Ultimate tier for 14.99$/month. [https://discord.com/discovery/applications/703886990948565003/store](https://web.archive.org/web/20250428132430/https://discord.com/discovery/applications/703886990948565003/store)
[^gdpr-3-1]: This is according to GDPR Article 3 (1)
[^gdpr-4-1]: This is according to GDPR Article 4 (1)
[^privacy-policy]: [https://docs.doublecounter.gg/double-counter-en/legal](https://web.archive.org/web/20250401032211/https://docs.doublecounter.gg/double-counter-en/legal)
[^publicly-sharing]: [image](/assets/blog/sharing-data.png)
[^bot-not-pii]: [image](/assets/blog/bot-not-pii.png)
[^telling-users-not-pii]: [image](/assets/blog/telling-users-not-pii.png)
[^gdpr-17]: This is according to GDPR Article 17
[^discord-api-id]: [https://discord.com/developers/docs/resources/user#get-user](https://discord.com/developers/docs/resources/user#get-user)
[^emails]: Phew, it's quite a few emails, we compiled a [ZIP file](/assets/blog/doublecounter-emails.zip) containing *all* original .eml files. On top of this, we provide an "easy-to-read" [text transcript](/assets/blog/full-email-transcript.txt).
[^discord-chat]: You can view the chat transcript we had with their support team [here](/assets/blog/transcript.txt)
[^gdpr-6-1-f]: This is according to GDPR Article 6 (1) (f)
[^old-data]: They [announced Doogle on 2024-09-19](/assets/blog/doogle-announcement.png), I check my own messages with DoubleCounter and checked with friends, no one received an information of their data now being used like that.
[^gdpr-12]: This is according to GDPR Article 12
[^gdpr-21-4]: This is according to GDPR Article 21 (4)
[^project-renaissance]: This poll was done on the Project: Renaissance Discord server. The server has 800 members. I would really like to thank Catchy, who is credited, for willing to make this poll!  


<!-- Modal -->
<div>
  <input type="checkbox" id="catchy-modal-toggle" style="display:none;">

  <div class="modal">
    <label for="catchy-modal-toggle" class="overlay"></label>
    <div class="popup">
      <label for="catchy-modal-toggle" class="close">&times;</label>
      <div class="modal-content">
        <img src="/assets/blog/catchy.webp" alt="Catchy avatar" class="avatar">
        <div class="info">
          <p class="username">@catchy_</p>
          <p class="tagline">on Discord</p>
        </div>
      </div>
    </div>
  </div>
</div>

<style>
.catchy-label {
  cursor: pointer; 
  color: #0066cc;
}
.catchy-label:hover {
  text-decoration: underline;
}
.modal {
  position: fixed;
  top: 0; left: 0;
  width: 100%; height: 100%;
  pointer-events: none;
  z-index: 999;
}
#catchy-modal-toggle:checked ~ .modal {
  pointer-events: all;
}
#catchy-modal-toggle:checked ~ .modal .overlay {
  background: rgba(0, 0, 0, 0.6);
  display: block;
}
#catchy-modal-toggle:checked ~ .modal .popup {
  opacity: 1;
  transform: translate(-50%, -50%) scale(1);
}

.overlay {
  position: fixed;
  top: 0; left: 0;
  width: 100%; height: 100%;
  display: none;
}

.popup {
  position: fixed;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%) scale(0.95);
  background: #2b2d31;
  padding: 1em 2em;
  border-radius: 12px;
  text-align: left;
  max-width: fit-content;
  box-shadow: 0 0 20px rgba(0,0,0,0.6);
  opacity: 0;
  transition: all 0.2s ease;
  z-index: 1000;
  color: #fff;
  font-family: 'Segoe UI', 'Open Sans', sans-serif;
}
@media (max-width: 600px) {
  .popup {
    padding: 1em;
  }
}
@media (max-width: 300px) {
  .popup {
    font-size: 0.8em;
    padding: 0.5em;
  }
}

.close {
  position: absolute;
  top: 0;
  right: 0.5em;
  font-size: 1.5em;
  cursor: pointer;
  color: #ccc;
}

.modal-content {
  display: flex;
  align-items: center;
  gap: 1em;
}

img.avatar{
  width: 64px;
  height: 64px;
  border-radius: 50%;
  max-width: 64px;
}

.username {
  margin: 0;
  font-size: 1.2em;
  font-weight: 600;
  color: #fff;
}

.tagline {
  margin: 0;
  font-size: 0.9em;
  color: #aaa;
}

</style>
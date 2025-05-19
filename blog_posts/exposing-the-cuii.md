Title: Exposing the CUII
Summary: A private organization controlling what websites to block in Germany-without courts, without transparency.
Date: 2024-12-18
Image: /assets/blog/cuii.png
Hash: cuii
---------
## What is the CUII?  

The *Clearingstelle Urheberrecht im Internet* (CUII) is a private organization established in Germany in 2021. 
Its members include ISPs like Deutsche Telekom, Vodafone, 1&1, and Telefónica (O2), alongside major copyright holders[^1]. 
These ISPs alone control over 85% of the German market[^2].  

The CUII's role is to block websites allegedly commiting copyright infringement. 
However, unlike traditional legal processes, the CUII bypasses courts entirely. 
Its members find websites they want blocked, the CUII "evaluates" this and then decide which ones to block 
without requiring judicial approval.  

One would assume that such a powerful entity operates transparently and adheres to strict monitoring practices, 
as outlined in their own Code of Conduct (Section 8)[^3]. Unfortunately, that's far from the case.  

---

## How it began: *cuiiliste.de*  

Although the CUII decides what websites to block, it does not publicly disclose the blocked domains. 
Even Germany's Federal Network Agency (BNetzA) is not informed about mirror domains 
(Section 9 of the Code of Conduct)[^3].  

To counter this secrecy, the website *cuiiliste.de* was created in 2021. 
It aimed to crowdsource a list of blocked domains[^4]. 
Sadly, *cuiiliste.de* shut down in 2023[^5].  

When I discovered this, I decided to revive the concept. 
I acquired the domain and automated the process of checking and monitoring blocked websites. This included monitoring when which ISP blocked or unblocked which domain.
This is because of the CUII's refusal to publish a domain list, as described in their Code of Conduct (Appendix 1, Section 4, Paragraph 4, Letter l)[^3].  

While I worked on this, my friend [Northernside](https://northernsi.de) **GOT HIS HANDS ON THE ACTUAL CUII DOMAIN LIST!?**  
We won't disclose how, but this was groundbreaking.

<img src="/assets/blog/domains.png" alt="CUII List">
<div class="subtext">holy shit, we actually have the cuii list. holy fucking bingle. what?!? :3</div>

---

## Publishing the list  

The leaked list revealed 284 blocked domains and subdomains. 
There are no wildcard blocks, all subdomains were individually listed.

Once the list was added to the database, news outlets picked up the story. 
Articles appeared on platforms like Netzpolitik.org[^6], Heise[^8], TorrentFreak[^9], and others. 
This made the project gained widespread attention, making the CUII’s lack of transparency more widely known.  

You can still view and contribute to the updated list at [cuiiliste.de](https://cuiiliste.de/).  

![CUII List](/assets/blog/cuiiliste.png)  

---

## The monitoring failure  

The CUII's members are **required** to monitor blocked websites regularly to ensure they still meet the criteria for blocking (Section 8 of the Code of Conduct)[^3]. 
This requirement is also enforced by the Federal Network Agency (BNetzA)[^10].  

![CUII Monitoring](/assets/blog/regelmaessiges-monitoring.png)  
<div class="subtext">
Translation: "The applicant [CUII member] has to carry out regular monitoring to check whether the conditions for the blocking claim according to §19a UrhG [German Copyright Act] still exist."<br>
- Statement from the Federal Network Agency (BNetzA) in a Freedom of Information Act request
</div>

Yet domains remained wrongfully blocked **for years**. 
For example, `serien.sx` redirected to non-infringing content (`serien.domains`) as early as April 2022 (over 2 and a half year!). 
Despite this, it remained blocked until I raised the issue with the CUII. 
While they never responded, the domain was quietly unblocked soon after.  

This was not an isolated case. 
Upon reviewing the blocked domains, I found that 41 out of 122 were wrongfully blocked-over one-third!  
News outlets like Netzpolitik.org reported on this[^11], forcing the CUII to lift many wrongful blocks[^12].

---

## Conclusion  

The CUII operates with little oversight, significant power, and a questionable track record.
Its members fail to perform required monitoring, leading to numerous wrongful blocks.
Transparency, the foundation of accountability, still remains absent.  

But how is such an organization even possible in Germany?
Net neutrality should, in theory, protect the openness of the internet, yet the existence of the CUII seems to circumvent this principle.
The pressure comes from legal and financial risks ISPs face if they do *not* block websites accused of copyright infringement.
Although the law **does not** mandate these blocks, the fear of potential lawsuits motivates ISPs to align 
with copyright holders and form private and secretive organizations like the CUII.  

This raises fundamental questions about the balance of power. 
How can private companies decide what is accessible on the internet? 
How does a system allow ISPs to bypass judicial oversight and enforce these measures themselves? 
And, most troubling, how did this lead to the creation of a secretive and unaccountable organization 
with such authority in a country that values freedom and transparency?  

Do we really want a future where private and secretive organizations decide what we can access online,
based on the whims of multi-billion-dollar companies?  
The CUII shows how power, even in a free country, can grow under the disguise of enforcing outdated and overly broad copyright laws.
Laws that increasingly prioritize corporate interests over individual freedoms, destroying the openness, 
innovation, and equality that the internet was meant to protect.
<br>
<br>

Visit [cuiiliste.de](https://cuiiliste.de/) to see the updated list and help push for more transparency in digital censorship (German only).


### Sources
[^1]: <a href="https://cuii.info/en/members/">cuii.info - members</a>, 2024 (<a href="https://web.archive.org/web/20240530000422/https://cuii.info/en/members/">Archive</a>)
[^2]: <a href="https://www.dslweb.de/telekom.php">DSLWEB</a>, 2024 (<a href="https://web.archive.org/web/20240621043036/https://www.dslweb.de/telekom.php">Archive</a>)
[^3]: <a href="https://cuii.info/fileadmin/files/CUII_CodeofConduct_23.pdf">CUII Code of Conduct</a>, 2023 (<a href="https://web.archive.org/web/20240823231253/https://cuii.info/fileadmin/files/CUII_CodeofConduct_23.pdf">Archive</a>)
[^4]: <a href="https://web.archive.org/web/20210331162058/https://cuiiliste.de/">web archive of cuiiliste.de</a>, 2021
[^5]: <a href="https://web.archive.org/web/20230610190529/http://cuiiliste.de/">web archive of cuiiliste.de</a>, 2023
[^6]: <a href="https://netzpolitik.org/2024/cuii-liste-diese-websites-sperren-provider-freiwillig/">Netzpolitik - "Diese Websites sperren Provider freiwillig"</a>, 2024
[^7]: <a href="https://winfuture.de/news,127228.html">winfuture - "17-Jähriger legt geheime Piraterie-Blockliste deutscher Provider offen"</a>, 2024
[^8]: <a href="https://heise.de/-9847202">Heise - "Netzsperren: Schüler kritisiert "Selbstjustiz" der Clearingstelle Urheberrecht"</a>, 2024
[^9]: <a href="https://torrentfreak.com/17-year-old-student-exposes-germanys-secret-pirate-site-blocklist-240822/">Torrentfreak - "17-Year-old Student Exposes Germany's ‘Secret' Pirate Site Blocklist"</a>, 2024
[^10]: <a href="https://media.frag-den-staat.de/files/foi/914902/anlage3stellungnahmegeschwrzt.pdf">FragDenStaat an BNetzA FOI914902-Anlage 3</a>, 2024 (<a href="https://web.archive.org/web/20240927204441/https://media.frag-den-staat.de/files/foi/914902/anlage3stellungnahmegeschwrzt.pdf">Archive</a>)
[^11]: <a href="https://netzpolitik.org/2024/cuii-viele-netzsperren-wirken-laenger-als-erlaubt/">Netzpolitik - "Viele Netzsperren wirken länger als erlaubt"</a>, 2024
[^12]: <a href="https://netzpolitik.org/2024/cuii-liste-internetprovider-heben-39-netzsperren-auf/">Netzpolitik - "Internetprovider heben 39 Netzsperren auf"</a>, 2024

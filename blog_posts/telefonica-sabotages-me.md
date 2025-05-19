Title: A German ISP tampered with their DNS - specifically to sabotage my website
Summary: One of Germany's biggest ISPs changed how their DNS works, right after I exposed an organization that they’re part of.
Date: 2025-02-26
Image: /assets/blog/sabotage.png 
Hash: sabotage
---------
## My website: Publishing Germany's secret internet blocklist
In Germany, we have the *Clearingstelle Urheberrecht im Internet* (CUII) - literally 'Copyright Clearinghouse for the Internet', 
a private organization that decides what websites to block, corporate interests rewriting our free internet.
No judges, no transparency, just a bunch of ISPs and major copyright holders deciding what your eyes can see.  
I decided to create a website, [cuiiliste.de](https://cuiiliste.de/), to find blocked domains, as the CUII refuses to publish such a list.
To read more about the CUII, check out [one of my previous blog posts](/blog/exposing-the-cuii). Germany's four biggest ISPs 
(Telekom, Vodafone, 1&1 and Telefonica (o2)) are all part of the CUII.

## Yet another slip-up by the CUII
This week, Netzpolitik.org published an article about the CUII's latest blunder[^1], based on information I gathered. 
They managed to block domains that no longer even existed: websites that had already been seized and taken offline when they were blocked.
It's not the first time the CUII has tripped over its own feet, and this mistake likely didn’t sit well with them.
In the past, it was *really* easy to find out if a domain was blocked by the CUII.
If you asked an ISP's DNS server (basically the internet's phone book) for a site and got a CNAME to `notice.cuii.info`, you knew it was blocked.  
What this basically means in case you're not a tech nerd:  
You can check the phone book of an ISP (the "DNS server") where to find a website, and you'd receive a note saying "This site is blocked by the CUII" if the page is blocked.
Automating this was simple, I could basically just ask "Hey, where can I find this site?" and immediately knew if it was blocked.
The CUII apparently did *not* like the fact that it was so easy for me to check if a domain was blocked. They want to keep their list secret.  
ISPs like Telekom, 1&1 and Vodafone actually all stopped using this response a few months ago, 
after older articles about the CUII's past failures were published. Instead, they started pretending that blocked sites didn't exist at all.
Straight up erasing entries from the phone book. You could not tell if a site was blocked or just didn't exist.
Telefonica (the parent company of for example o2, Germany's **fourth-biggest ISP**[^2]), apparently didn't get this memo, and they still used `notice.cuii.info` in their DNS responses.  
    
On cuiiliste.de, anyone can enter a domain, and see if it is blocked by the CUII, and which ISPs block it specifically.

### I get a new visitor
Telefonica modified their DNS servers, specifically saying that `blau-sicherheit.info` was blocked by the CUII.
At 11:06 AM last Friday, someone from Telefonica's network checked if `blau-sicherheit.info` was blocked on my site. 
The twist? Telefonica seems to own this domain. Blau is one of their brands[^3], and `blau-sicherheit.info` wasn’t some piracy hub -
it appears to be a test domain of theirs. 
My tool flagged it as blocked because Telefonica's DNS servers said so. 
Why would they block their own domain?

![Telefonica's DNS response](/assets/blog/blau-sicherheit-probe.png)
To recap:
<ul>
    <li> Telefonica blocks their own domain</li>
    <li> Someone from Telefonica visits my website to check if I detect this</li>
    <li> I <i>do</i> in fact detect this</li>
</ul>

### Telefonica modifies how their blocking works... to mess specifically with my website
Two hours after this suspicious query, I was bombarded with Notifications. 
My program thought that the CUII had suddenly unblocked hundreds of domains.  
The reason: Telefonica had altered their DNS servers to stop redirecting blocked domains to `notice.cuii.info`.
Now they pretend that the domain doesn't exist at all, after they *specifically* blocked their own domain, likely to find out how my website works.  
I had to spend my entire Friday afternoon fixing this mess, and now everything is fully operational again.
![Git pull](/assets/blog/git-pull.png)
The fix worked, but there’s a catch: without the `notice.cuii.info` redirect, it's harder to confirm if a block is actually the CUII's doing. 
Sometimes ISPs block sites for other reasons, like terrorism content ([I wrote about that too](/blog/german-isps-block-terrorist-content)). 
I try to compensate this by cross-checking domains against a list of known non-CUII-blocks.
![Probing a site blocked by ISPs, but not by the CUII](/assets/blog/almanar-blocked.png)

### Why sabotage my website?
The timing is more than suspicious. 
Right after Netzpolitik’s article exposed the CUII for blocking non-existent domains, they make it harder to track their mistakes. 
Coincidence? Or a move to bury future slip-ups? 
We can only speculate.
Regardless of intent, the result is the same: less transparency and harder oversight. And that benefits the CUII, not the public.  
  
  
In this context, Netzpolitik.org released another article (German): 
[Netzpolitik.org: Provider verstecken, welche Domains sie sperren](https://netzpolitik.org/2025/netzsperren-provider-verstecken-welche-domains-sie-sperren/)

### Sources
[^1]: [Netzpolitik: 17-Jähriger treibt die CUII vor sich her (German)](https://netzpolitik.org/2025/netzsperren-17-jaehriger-treibt-die-cuii-vor-sich-her/)
[^2]: [DSLWEB, Übersicht: Aktuelle Marktanteile Breitband](https://www.dslweb.de/breitband-report-deutschland.php)
[^3]: [Telefonica: Blau (German)](https://www.telefonica.de/kunden/blau.html)
Swift Arrow Couriers - Tracking Window

What this does
-------------------------------------------------------------------------------------------------------
This is a command-line program that replaces the old paper window at
Swift Arrow's tracking office. Staff sign in once and get a "day
pass" instead of typing their password every single time. After
that, they type slips like GET parcel <code> or PUT parcel <code>,
and every reply starts with a status code, the same way a real API
responds (200, 404, and so on).

There are 50,000 parcels in the dataset. To keep things fast, I built
three lookup tables (I call them indexes) instead of scanning the
whole list every time - one by tracking code, one by destination
city, and one by status. There's also a small cache that remembers
the last 10 answers so repeat questions come back instantly, and a
"seal" that checks whether the saved file has been tampered with.

Folder structure
--------------------------------------------------------------------------------------------------------
swift_arrow/ - the actual package, everything the program does lives
in here.

- __init__.py - just marks the folder as a package, empty otherwise.
- storage.py - loads and saves parcels.json, builds the three
  indexes, and handles the seal (checking the file hasn't been
  quietly edited).
- auth.py - checks passwords against their hashes, issues and checks
  day-pass tokens, and knows who's allowed to delete.
- parcels.py - the actual GET/POST/PUT/DELETE logic for parcels,
  using the index so lookups are fast, and timing how long each one
  takes.
- cache.py - the "tray." Keeps the 10 most recent answers so repeat
  questions don't redo the work.
- stats.py - counts how many times each tracking code gets looked
  up, for the most-wanted board.

Outside the package:
- main.py - the only file you actually run. It just reads slips and
  calls functions from swift_arrow. No real logic lives here.
- seed_staff.py - run this once before using the program for the
  first time. It turns the plaintext staff list into hashed
  passwords. I don't push this file to GitHub since it has real
  passwords in it before they get hashed.
- staff_credentials.json - gets created by seed_staff.py. Only holds
  hashed passwords, never the real ones.
- parcels.json - the given dataset, gets updated as the program runs.
- parcels.seal - created automatically, holds a fingerprint of
  parcels.json so tampering can be caught.
- .gitignore - keeps seed_staff.py and __pycache__ out of git.

How to run it
----------------------------------------------------------------------------------------------------
First time only:
    python seed_staff.py

Every time after that:
    python main.py

Sign in when it asks. You'll get a day pass back - you don't need to
type your password again after that, the program remembers it for
the rest of that run.

Slips you can type
------------------------------------------------------------------------------------------------------
    GET parcel <tracking code>
    GET parcels to <city>
    GET parcels <status>          e.g. GET parcels out for delivery
    GET board
    PUT parcel <tracking code>
    DELETE parcel <tracking code>

PUT will ask you for a new status and/or destination. Leave either
one blank to keep it as it was.

What the codes mean
---------------------------------------------------------------------------------------------------
200 - done, here's your answer
201 - created something new
400 - couldn't understand that slip
401 - not signed in, your pass expired, or the ledger failed its
tamper check
403 - you're signed in, but not allowed to do that (a Clerk trying
to delete)
404 - no such parcel

Who can do what
-----------------------------------------------------------------------------------------------
Clerks can look up parcels and update them. Only the Station Master
can delete one. If a Clerk tries, they get a 403.

Why the indexes matter
---------------------------------------------------------------------------------------------------
Without them, looking up one parcel out of 50,000 means checking
every single one until you find it, or checking all of them and
finding nothing. That gets slow. A dictionary lookup by key doesn't
work that way - it jumps straight to the answer no matter how big
the dictionary is, which is why GET parcel <code> comes back in a
fraction of a millisecond even against the full file. The city and
status indexes work the same way, just grouped differently.

Why there's a cache
-------------------------------------------------------------------------------------------------
People ask the same question more than once. Rather than redoing a
city or status search every time, the last 10 answers are kept in
memory and handed back instantly if the same question comes in
again. This barely matters for single-parcel lookups since those are
already near-instant, but it makes a real difference on city/status
searches that touch thousands of parcels.

Any time a parcel gets changed through PUT or DELETE, the cache and
both group indexes (city and status) get rebuilt from scratch. If I
didn't do this, you could end up with a cached answer that's flat
out wrong, or a parcel still showing up under a city or status it no
longer belongs to.

Hashing - two different jobs, two different tools
------------------------------------------------------------------------------------------------------
This project uses hashing for two completely different things, and I
used a different tool for each on purpose.

Passwords are hashed with bcrypt. When someone signs in, their typed
password gets scrambled and compared to the stored scrambled version
- the real password is never written anywhere. bcrypt is deliberately
slow, which makes it impractical for someone to brute-force guess a
password, and it automatically mixes in some randomness (a salt) so
two people with the same password don't end up with matching hashes.

Checking whether the ledger's been tampered with uses sha256
instead, which is fast rather than slow. Here speed isn't a problem,
because I'm not trying to stop someone from guessing anything - I
just want to know quickly if the file changed at all. Every time the
program saves, it also saves a fresh fingerprint of the file. At
startup, it recomputes that fingerprint and compares it to what was
saved. Change even one character anywhere in the file and the
fingerprint comes out completely different, which is how the seal
catches tampering that wouldn't even break the JSON.

Day passes (tokens)
-----------------------------------------------------------------------------------------------
When you sign in, the program generates a random, unguessable token
using Python's secrets module (not the regular random module, which
isn't meant for anything security related). That token is tied to
your username and role and only lives in memory while the program is
running - it's never saved to a file, which is also why it never
ends up on GitHub. It expires 5 minutes after being issued; after
that you'll get a 401 and be asked to sign in again.

Most-wanted board
--------------------------------------------------------------------------------------------------
Every time someone looks up a specific parcel by tracking code, that
gets counted. GET board shows the 10 most-looked-up tracking codes
and how many times each came up. These counts live in memory only,
so they reset every time the program restarts.

What happens if the data gets damaged
----------------------------------------------------------------------------------------------------
If parcels.json gets broken badly enough that it's no longer valid
JSON, the program won't crash - it prints a warning and just starts
with an empty parcel list.

That's different from tampering. If the file is still valid JSON but
doesn't match the saved seal (meaning something inside it got
changed since the last real save), the program refuses to load the
parcel data at all and says so. You can still sign in and use the
menu, but nothing parcel-related works until the file is fixed or
replaced.

Things I know are limited
-----------------------------------------------------------------------------------------------------
- City and status names have to match exactly, including
  capitalization.
- The dataset is basically static for this project - POST parcel
  exists in the code, but new parcels aren't really part of what
  gets tested.
- Most-wanted counts don't get saved anywhere, so they reset every
  restart.
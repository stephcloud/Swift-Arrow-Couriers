Swift Arrow Couriers — Tracking Window
=========================================

What this is
--------------
A command-line program that replaces the old paper tracking window.
Staff sign in once and receive a day pass instead of typing a password
every time. From then on, they submit slips (GET/POST/PUT/DELETE
commands) and get back a reply that always starts with a status code,
the same way a real web API responds. A 50,000-parcel dataset is kept
in memory with three indexes for instant lookup — by tracking code, by
destination city, and by status — plus a small cache that remembers
the ten most recent answers, and a seal that detects if the saved
ledger has been tampered with.

Folder structure
-------------------
swift_arrow/              The package. All program logic lives here.
    __init__.py             Marks this folder as a Python package.
    storage.py                Loads and saves parcels.json. Builds all
                            three indexes (tracking code, destination
                            city, status). Computes and checks the
                            seal — a fingerprint of the ledger's
                            contents.
    auth.py                     Checks hashed passwords, issues and
                            validates day-pass tokens (with 5-minute
                            expiry), and checks whether a user is the
                            Station Master.
    parcels.py                   GET/POST/PUT/DELETE logic for one
                            parcel or a group of parcels, using the
                            index for fast lookup and timing how long
                            each lookup takes.
    cache.py                      The "tray" — remembers the ten most
                            recently answered questions, so a repeated
                            question is answered instantly instead of
                            being searched again.
    stats.py                       Counts how often each tracking code
                            is looked up, for the most-wanted board.

main.py                   The only file you run. Parses slips and
                        calls functions from the swift_arrow package.
                        Contains no logic of its own beyond the
                        window loop.

seed_staff.py             Run once, before the program is used for the
                        first time. Converts the plaintext staff table
                        into hashed credentials. This file is NOT
                        pushed to GitHub (see .gitignore) because it
                        contains real plaintext passwords used only to
                        generate the hashes.

staff_credentials.json    Created by seed_staff.py. Contains only
                        scrambled password hashes and each staff
                        member's position. No real password is ever
                        stored here or anywhere else in the project.

parcels.json               The given 50,000-parcel dataset. Loaded at
                        startup, updated in place, and saved back to
                        this same file after any change.

parcels.seal                Created automatically. Holds a fingerprint
                        of parcels.json, checked at every startup to
                        detect tampering.

.gitignore                  Excludes seed_staff.py and __pycache__/
                        from version control.

README.txt                   This file.

How to run
-------------
First time only:
    python seed_staff.py

Then, every time:
    python main.py

You will be asked to sign in. Successful sign-in returns a day pass
(token). Show no further password after that; the token is held for
the rest of that session and checked on every slip automatically.

Slip format
--------------
    GET parcel <tracking code>
    GET parcels to <city>
    GET parcels <status, e.g. out for delivery>
    GET board
    PUT parcel <tracking code>
    DELETE parcel <tracking code>

PUT will prompt for a new status and/or destination, either of which
can be left blank to leave that field unchanged.

Reply codes
--------------
200   Done, here you are.
201   Created, a new thing now exists.
400   The slip could not be read.
401   Not signed in, the day pass has expired or is invalid, or the
      ledger failed its tamper check.
403   Signed in, but not allowed to do this (a Clerk attempting
      DELETE).
404   There is no such parcel.

Roles
--------
Clerks can look up and update parcels. Only the Station Master can
delete a parcel; a Clerk attempting DELETE is refused with a 403.

The indexes — why lookups are fast
--------------------------------------
Rather than searching through all 50,000 parcels for a match,
storage.py builds a dictionary once at startup mapping each tracking
code directly to its parcel. Looking something up in a dictionary by
its key takes roughly the same amount of time no matter how large the
dictionary is, which is why GET parcel <code> returns in a fraction
of a millisecond even against the full dataset. Two more dictionaries
do the same for destination city and for status, so GET parcels to
<city> and GET parcels <status> do not need to scan the whole list
either.

The cache — why some answers are remembered
-------------------------------------------------
Customers often ask the same question more than once. The ten most
recently answered questions are kept in memory. Asking the same
question again is answered directly from this cache instead of being
recalculated, which matters most for city and status lookups, where
gathering potentially thousands of matches is real work. A single
parcel lookup is already fast enough that the cache makes no
measurable difference there.

Whenever a parcel is changed through PUT or DELETE, the cache, the
destination-city index, and the status index are all rebuilt. This
prevents staleness in three different ways: a cached answer describing
data that no longer matches reality, a parcel remaining listed under a
city it no longer belongs to after its destination changes, and the
same for a status that has since changed.

Hashing — the different jobs it does in this project
------------------------------------------------------------
Hashing is used for two different jobs here, with two different tools,
because the two jobs need different properties from a hash function.

Password storage uses bcrypt. A password typed at sign-in is scrambled
and compared against the stored scrambled version; the real password
is never written to any file. bcrypt is deliberately slow, which makes
guessing passwords by brute force impractical, and it automatically
adds random data (a salt) so that two staff members with the same
password do not end up with identical-looking stored hashes.

Detecting tampering with the ledger uses sha256, a fast general-purpose
hash. Speed is not a weakness here, since the goal is not to resist
guessing but to notice quickly whether the file's contents have
changed at all. A fingerprint of the whole file is computed and saved
after every legitimate save; at every startup, the fingerprint is
recomputed and compared. Even a single changed character anywhere in
the file produces a completely different fingerprint, which is what
lets the seal catch tampering that would otherwise still look like
valid, readable JSON.

Day pass (token)
-------------------
Signing in successfully issues a random, unguessable token using
Python's secrets module, which is built for security-sensitive
randomness (unlike the general-purpose random module). The token maps
to the signed-in user's identity and role, held only in memory for
that run of the program — never written to disk, which is also why
day passes are never pushed to GitHub; there is nothing to push. A
token expires 5 minutes after it is issued; a slip presented with an
expired token receives a 401 and the user is asked to sign in again.

The most-wanted board
-------------------------
Every time a specific tracking code is looked up, the count for that
code is incremented in memory. GET board shows the ten most-looked-up
tracking codes and how many times each was asked about. These counts
reset when the program restarts, since they are not saved to disk.

Data corruption and tampering
----------------------------------
If parcels.json has been damaged so that it is no longer valid JSON,
the program does not crash. It prints a warning and starts with an
empty parcel list rather than losing the ability to run.

Separately, if parcels.json is still valid JSON but its contents no
longer match the saved seal (meaning something inside it was edited
since the last legitimate save), the program refuses to load the
parcel data at all rather than trust it, and says so plainly. Signing
in and using the menu still work; parcel data does not load until a
clean file is restored.

Known limitations
---------------------
- City and status names in GET parcels <...> are matched exactly as
  typed, including capitalization.
- The dataset is treated as effectively static; POST parcel exists in
  the code but new parcels are not part of the ledger the program is
  tested against.
- Most-wanted counts are memory-only and reset on restart.
Swift Arrow Couriers — Tracking Window
=========================================

What this is
--------------
A command-line program that replaces the old paper tracking window.
Staff sign in once and receive a day pass instead of typing a password
every time. From then on, they submit slips (GET/POST/PUT/DELETE
commands) and get back a reply that always starts with a status code,
the same way a real web API responds. A 50,000-parcel dataset is kept
in memory with an index for instant lookup by tracking code, a second
index for instant lookup by destination city, and a small cache that
remembers the ten most recent answers.

Folder structure
-------------------
swift_arrow/              The package. All program logic lives here.
    __init__.py             Marks this folder as a Python package.
    storage.py                Loads and saves parcels.json. Builds the
                            two indexes: one by tracking code, one by
                            destination city.
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
    PUT parcel <tracking code>
    DELETE parcel <tracking code>

PUT will prompt for a new status and/or destination, either of which
can be left blank to leave that field unchanged.

Reply codes
--------------
200   Done, here you are.
201   Created, a new thing now exists.
400   The slip could not be read.
401   Not signed in, or the day pass has expired or is invalid.
403   Signed in, but not allowed to do this (a Clerk attempting
      DELETE).
404   There is no such parcel.

Roles
--------
Clerks can look up and update parcels. Only the Station Master can
delete a parcel; a Clerk attempting DELETE is refused with a 403.

The index — why lookups are fast
------------------------------------
Rather than searching through all 50,000 parcels for a match,
storage.py builds a dictionary once at startup mapping each tracking
code directly to its parcel. Looking something up in a dictionary by
its key takes roughly the same amount of time no matter how large the
dictionary is, which is why GET parcel <code> returns in a fraction
of a millisecond even against the full dataset. A second dictionary
does the same for destination cities, so GET parcels to <city> does
not need to scan the whole list either.

The cache — why some answers are remembered
-------------------------------------------------
Customers often ask the same question more than once. The ten most
recently answered questions are kept in memory. Asking the same
question again is answered directly from this cache instead of being
recalculated, which matters most for GET parcels to <city>, where
gathering potentially thousands of matches is real work. A single
parcel lookup is already fast enough that the cache makes no
measurable difference there.

Whenever a parcel is changed through PUT or DELETE, both the cache
and the destination-city index are rebuilt. This prevents two
different staleness problems: a cached answer describing data that no
longer matches reality, and a parcel remaining listed under a city it
no longer belongs to after its destination changes.

Hashing — the different jobs it does in this project
------------------------------------------------------------
Hashing is used for one purpose in this project: password storage.
A password typed at sign-in is scrambled with bcrypt and compared
against the stored scrambled version; the real password is never
written to any file. bcrypt is used instead of a general-purpose hash
because it is deliberately slow, which makes guessing passwords by
brute force impractical, and it automatically adds random data (a
salt) so that two staff members with the same password do not end up
with identical-looking stored hashes.

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

Data corruption
-------------------
If parcels.json has been damaged, the program does not crash. It
prints a warning and starts with an empty parcel list rather than
losing the ability to run.

Known limitations
---------------------
- City names in GET parcels to <city> are matched exactly as typed,
  including capitalization.
- The dataset is treated as effectively static; POST parcel exists in
  the code but new parcels are not part of the ledger the program is
  tested against.
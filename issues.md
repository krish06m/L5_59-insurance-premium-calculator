# Issues Found — `premium_calculator.py`

Line numbers refer to the **original** file (commit `64fc863`). Issues were
found with Pylint, Bandit and Flake8, and by checking the program's output.

| Metric | Before | After |
|--------|--------|-------|
| Pylint score | 5.73/10 | 10.00/10 |
| Bandit issues (High / Medium / Low) | 1 / 5 / 4 | 0 / 0 / 0 |
| Flake8 violations | 19 | 0 |

## Issue Table

Sorted by severity (High → Medium → Low). Every issue below has been fixed.

| # | Issue | Type | Line(s) | Description | Fix Approach | Severity |
|---|-------|------|---------|-------------|--------------|----------|
| 1 | Unsafe tar extraction (path traversal) | Bandit B202 | 63–65 | `tar.extractall()` on a customer-uploaded archive with no checks. A member named `../../etc/x` or an absolute path can write files outside `claims_docs`. | Use `with tarfile.open(...)` and `extractall("claims_docs", filter="data")`. The `data` filter rejects absolute paths, `..`, links that escape the folder, and device files. | High |
| 2 | Hard-coded secret token | Bandit B105 | 13, 103 | `UNDERWRITER_TOKEN = "uw-7f3a9c2e1b"` is stored in source control and repeated in `main()`. | Read it from the `UNDERWRITER_TOKEN` environment variable. If the variable is empty, nobody is authorised. | High |
| 3 | TLS certificate verification disabled | Bandit B323 / Pylint W0212 | 58 | `ssl._create_unverified_context()` turns off certificate and hostname checks, so the rate download can be intercepted (MITM). It also uses a protected member. | Use `ssl.create_default_context()`. | High |
| 4 | XML parsed with the standard library | Bandit B405, B314 | 7, 48 | `xml.etree.ElementTree` is vulnerable to entity-expansion attacks such as "billion laughs" when it parses untrusted partner XML. | Use `defusedxml.ElementTree`. | Medium |
| 5 | Mutable default argument changes later quotes | Pylint W0102 (logic bug) | 17, 27 | `discounts=[]` is shared between calls, and the function appends `500` to it. The second identical quote therefore came out at **5500** instead of **6000**. | Use `discounts=None` and create a new list inside the function. Never mutate the caller's list. | Medium |
| 6 | String `"no"` treated as smoker | Logic bug (no tool flags it) | 92, 22 | `calculatePremium(..., "no", ...)` was called. `"no"` is truthy, so a non-smoker paid the 1.3× loading (**7970** instead of **6900**). | Pass `False` in `main()`. `calculate_premium` now raises `TypeError` if `smoker` is not a `bool`. | Medium |
| 7 | Discounts can make the premium negative | Logic bug | 25–26, 93 | Stacked discounts gave a life premium of **-800.0**. | Use `premium -= sum(discounts)` and clamp the result with `max(0.0, premium)`. | Medium |
| 8 | Age ignores whether the birthday has happened yet | Logic bug | 30–34 | `today.year - born.year` is one year too high before the birthday. 31-12-1990 gave **36** instead of **35**. A future DOB gave a negative age. | Subtract `(today.month, today.day) < (born.month, born.day)`. Raise `ValueError` for a future DOB. | Medium |
| 9 | Renewal crashes on 29 February | Logic bug | 79–81 | `date.replace(year=date.year + years)` raises `ValueError` for `2024-02-29`. The variable name `date` would also shadow `datetime.date`, which the fixed code imports. | Rename the variable to `start_date`. Catch `ValueError` and fall back to 28 February. | Medium |
| 10 | Monthly instalment collects less than the premium | Logic bug | 67–71 | `math.floor(premium / months)` drops the remainder. For 8000/12, twelve payments of 666 total 7992. `months=0` silently returned the full premium, and negative months were accepted. | Round up to the next paisa with `math.ceil`, giving 666.67. Raise `ValueError` if `months <= 0`. | Medium |
| 11 | Binding to all interfaces | Bandit B104 | 12 | `HOST = "0.0.0.0"` exposes the service on every network interface. | Use `127.0.0.1` by default. | Medium |
| 12 | Insecure temp-file path | Bandit B108 | 14 | `/tmp/premium_quotes.log` is world-writable and predictable, so it is open to symlink attacks. | Write the log in the working directory (`premium_quotes.log`). | Medium |
| 13 | URL opened without scheme check or timeout | Bandit B310 | 59 | `urlopen` accepts `file://` and custom schemes and has no timeout. The response is never closed. | Allow only `http` and `https`, set `timeout=10`, and use `with`. Mark the line `# nosec B310` with a comment explaining why. | Medium |
| 14 | Predictable policy numbers | Bandit B311 | 37 | `random.randint` is not cryptographically secure, so policy numbers can be guessed. Duplicate numbers could also overwrite existing quotes. | Use `secrets.randbelow()`. Regenerate the number if it already exists in `quotes`. | Low |
| 15 | Bare `except` and silent `continue` | Pylint W0702 / Flake8 E722 / Bandit B112 | 53–54 | A bare `except:` also swallows `KeyboardInterrupt`, `SystemExit` and real bugs. | Catch only `(TypeError, ValueError)`, which are the errors bad attribute values cause. | Low |
| 16 | Token compared with `==` | Security / Pylint R1703, R1705 | 73–77 | A plain string comparison is open to timing attacks. The `if/else` also returns `True`/`False` instead of just returning the condition. | Return `bool(UNDERWRITER_TOKEN) and secrets.compare_digest(...)`. | Low |
| 17 | File opened without `with` or encoding | Pylint R1732, W1514, C0209 | 42–44 | The file is not closed if `write` fails. The encoding depends on the platform. Formatting uses old-style `%`. | Use `with open(LOG_FILE, "a", encoding="utf-8")` and an f-string. | Low |
| 18 | Non-snake_case names | Pylint C0103 | 17, 30, 36, 39, 47, 57, 61, 67, 73, 79, 83 | Functions used camelCase (`calculatePremium`, `ageFromDob`, ...), which breaks PEP 8. | Rename to snake_case (`calculate_premium`, `age_from_dob`, ...). | Low |
| 19 | Missing docstrings | Pylint C0114, C0116 | 1 and every `def` | No module docstring and no function docstrings. | Add a module docstring and a one-line docstring to each function. | Low |
| 20 | PEP 8 layout | Flake8 E302, E305, E501 / Pylint C0301 | 14, 17, 52, 87, 101, 107 | Only one blank line between functions. Lines were up to 148 characters long. | Use two blank lines between top-level definitions and wrap long lines to 79 characters or less. | Low |
| 21 | Code runs on import | Style / Flake8 E305 | 107 | `main()` was called at module level, so importing the module ran the whole workflow and wrote to the log. | Wrap the call in `if __name__ == "__main__":`. | Low |
| 22 | Non-idiomatic loop | Pylint C0200 | 85–87 | `for i in range(len(keys))` indexing. | Use `enumerate(quotes, start=1)`. | Low |

## Output Before vs After

| Output line | Before | After | Correct? |
|-------------|--------|-------|----------|
| Quote 2 (same details as Quote 1) | 5500.0 | 6000.0 | Yes, matches Quote 1 |
| Non-smoker aged 50 | 7970.0 | 6900.0 | Yes, no smoker loading |
| Life with stacked discounts | -800.0 | 0.0 | Yes, never negative |
| Age from DOB 31-12-1990 (on 2026-10-15) | 36 | 35 | Yes, birthday not reached |
| Monthly instalment | 664 (7970 / 12, floored) | 575.0 (6900 / 12) | Yes, rounds up (8000 / 12 → 666.67, not 666) |
| Authorised | True (hard-coded token) | False unless `UNDERWRITER_TOKEN` is set | Yes |
| Server would listen on | 0.0.0.0 | 127.0.0.1 | Yes |

## Suppressions

- `# pylint: disable=too-many-arguments,too-many-positional-arguments` on
  `calculate_premium`. The six positional parameters are the existing public
  interface, and `main()` and other callers depend on them.
- `# nosec B310` on `urlopen`. This is a false positive because the URL scheme is
  checked against `{"http", "https"}` just before the call.

hits = [2,8,9,10,14,15,17,18,19,20,21,22,23,26,27,34,35,36,41,42,44,45]
total = 69
for window in (2, 3, 4):
    padded = set()
    for p in hits:
        start = max(1, p - window)
        end = min(total, p + window)
        padded.update(range(start, end + 1))
    pages = sorted(padded)
    # collapse into ranges
    ranges = []
    s = pages[0]
    prev = pages[0]
    for p in pages[1:]:
        if p == prev + 1:
            prev = p
            continue
        ranges.append((s, prev))
        s = p
        prev = p
    ranges.append((s, prev))
    covers31 = any(s <= 31 <= e for s, e in ranges)
    print(f"window={window}: ranges={ranges}  covers page31={covers31}")

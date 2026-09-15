"""Conservative paragraph editing for overlong generated essays."""
import re
from collections import Counter
from .service import word_count

def fit_essay(text, maximum=1400):
    """Remove redundant non-lead prose only; never cut a sentence or list."""
    blocks = re.split(r'\n\s*\n', text.strip())
    protected = set()
    next_lead = True
    last_heading = -1
    for i, block in enumerate(blocks):
        if re.match(r'^#{1,6}\s', block):
            protected.add(i)
            next_lead = True
            last_heading = i
        elif next_lead:
            protected.add(i)
            next_lead = False
        if re.match(r'^\s*(?:[-*+] |\d+[.)] )', block):
            protected.add(i)
    # Keep the complete final takeaway, plus the opening.
    protected.update(range(max(last_heading, 0), len(blocks)))
    kept = list(range(len(blocks)))
    removed = 0
    while word_count('\n\n'.join(blocks[i] for i in kept)) > maximum:
        candidates = [i for i in kept if i not in protected]
        total = word_count('\n\n'.join(blocks[i] for i in kept))
        candidates = [i for i in candidates if total-word_count(blocks[i]) >= 1100]
        if not candidates:
            break
        tokens = {i:set(re.findall(r'[a-z]{3,}',blocks[i].lower())) for i in kept}
        frequencies = Counter(token for group in tokens.values() for token in group)
        def redundancy(i):
            return (sum(frequencies[t]>1 for t in tokens[i])/max(1,len(tokens[i])), word_count(blocks[i]))
        kept.remove(max(candidates,key=redundancy))
        removed += 1
    return '\n\n'.join(blocks[i] for i in kept), removed

from __future__ import annotations

from collections import Counter

from lib_derushage import load_segments, total_score


if __name__ == "__main__":
    segments = load_segments()
    print("Synthese des extraits")
    print("====================")
    print(f"Total: {len(segments)}")
    print("Par statut:")
    for status, count in Counter(item["statut"] for item in segments).items():
        print(f"- {status}: {count}")
    print("Scores:")
    for segment in sorted(segments, key=total_score, reverse=True):
        print(f"- {segment['id']}: {total_score(segment)}/12")


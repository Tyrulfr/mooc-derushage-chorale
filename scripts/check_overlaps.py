from __future__ import annotations

from lib_derushage import find_overlaps, load_segments


if __name__ == "__main__":
    overlaps = find_overlaps(load_segments())
    if not overlaps:
        print("Aucun chevauchement detecte.")
    else:
        print("Chevauchements detectes:")
        for overlap in overlaps:
            print(
                f"- {overlap.first_id} / {overlap.second_id} "
                f"({overlap.chercheur}, {overlap.source}) sur {overlap.duree}s"
            )


import json
from pathlib import Path

import pymupdf


DATASET_DIR = Path(__file__).resolve().parent / "datasets"
DOCUMENT_DIR = DATASET_DIR / "documents"
CATALOG_PATH = DATASET_DIR / "catalog.json"


DOCUMENTS = [
    {
        "document_id": "DOC026",
        "title": "Municipal Water Treatment Operations Guide",
        "split": "development",
        "pages": [
            (
                "Water Treatment Overview",
                """
The fictional Brookfield water treatment facility processes
approximately 12 million liters of water each day.

The treatment process consists of four primary stages:
coagulation, sedimentation, filtration, and disinfection.

During coagulation, aluminum sulfate is added to help
suspended particles form larger clusters.

The sedimentation tanks provide an average settling time
of four hours before water enters the filtration system.
"""
            ),
            (
                "Filtration and Monitoring",
                """
The facility operates six rapid sand filters.

Each filter contains layers of sand and gravel that remove
remaining suspended particles.

Operators inspect filter performance every two hours.

The internal operating target for filtered water turbidity
is below 0.3 NTU.

Filters are backwashed every 48 hours or whenever the
pressure difference exceeds the facility's operating limit.
"""
            ),
            (
                "Maintenance and Emergency Procedures",
                """
Preventive maintenance inspections are conducted monthly.

Water quality instruments are calibrated every 14 days.

The facility maintains a backup generator capable of
supporting essential operations for 72 hours.

During a power failure, operators prioritize maintaining
disinfection and monitoring equipment.

All maintenance activities are recorded in a digital log
and reviewed by the operations supervisor every Friday.
"""
            )
        ]
    },
    {
        "document_id": "DOC027",
        "title": "Warehouse Inventory Management Handbook",
        "split": "test",
        "pages": [
            (
                "Warehouse Operations",
                """
The fictional Northfield distribution center contains
24 storage aisles and 1,200 pallet positions.

Incoming shipments are inspected at the receiving dock
before being entered into the inventory system.

Products are assigned unique stock keeping units, also
known as SKUs, for identification and tracking.

The warehouse uses the first-in, first-out method for
products with expiration dates.

High-demand products are stored near the dispatch area.
"""
            ),
            (
                "Inventory Control",
                """
Inventory cycle counts are performed every Wednesday.

The target inventory accuracy is 99.5 percent.

Products are classified into three groups using ABC
inventory analysis.

Category A contains high-value products that require
frequent monitoring.

Category B contains products of moderate value.

Category C contains lower-value products that require
less frequent monitoring.

Reorder alerts are generated when stock levels reach
the predetermined minimum quantity.
"""
            ),
            (
                "Shipping and Performance",
                """
Customer orders received before 2 PM are scheduled
for same-day dispatch.

The warehouse aims to maintain an order fulfillment
accuracy of at least 98 percent.

Damaged products are moved to a designated quarantine
area until an inspection is completed.

Shipping records are retained for three years.

Warehouse performance is reviewed monthly using
inventory accuracy, order fulfillment accuracy,
and average processing time.
"""
            )
        ]
    }
]


def create_scanned_pdf(document, destination):
    if destination.exists():
        print(f"Using existing {destination.name}")
        return

    scanned = pymupdf.open()

    try:
        for heading, content in document["pages"]:
            with pymupdf.open() as original:
                page = original.new_page(
                    width=595,
                    height=842
                )

                page.insert_text(
                    (50, 65),
                    heading,
                    fontsize=20,
                    fontname="hebo"
                )

                remaining = page.insert_textbox(
                    pymupdf.Rect(50, 100, 545, 780),
                    content.strip(),
                    fontsize=12,
                    fontname="helv"
                )

                if remaining < 0:
                    raise ValueError("Page content does not fit")

                image = page.get_pixmap(
                    dpi=150,
                    alpha=False
                )

                scanned_page = scanned.new_page(
                    width=595,
                    height=842
                )

                scanned_page.insert_image(
                    scanned_page.rect,
                    pixmap=image
                )

        scanned.set_metadata({
            "title": document["title"],
            "author": "Synthetic Benchmark Dataset"
        })

        scanned.save(
            destination,
            garbage=4,
            deflate=True,
            no_new_id=True
        )

    finally:
        scanned.close()

    print(f"Created {destination.name}")


def generate_documents():
    DOCUMENT_DIR.mkdir(parents=True, exist_ok=True)

    catalog = json.loads(
        CATALOG_PATH.read_text(encoding="utf-8-sig")
    )

    existing_ids = {
        document["document_id"]
        for document in catalog
    }

    for document in DOCUMENTS:
        document_id = document["document_id"]
        filename = f"{document_id}.pdf"
        destination = DOCUMENT_DIR / filename

        create_scanned_pdf(document, destination)

        with pymupdf.open(destination) as pdf:
            if len(pdf) != len(document["pages"]):
                raise ValueError("Unexpected page count")

            for page in pdf:
                if page.get_text().strip():
                    raise ValueError(
                        "PDF contains embedded text"
                    )

            print(
                f"{document_id}: {len(pdf)} image-only pages"
            )

        if document_id not in existing_ids:
            catalog.append({
                "document_id": document_id,
                "title": document["title"],
                "publisher": "Synthetic Benchmark Dataset",
                "category": "scanned",
                "split": document["split"],
                "filename": filename,
                "source_url": None,
                "manual_download": True,
                "synthetic": True,
                "generation_script":
                    "evaluation/generate_scanned_documents.py"
            })

            existing_ids.add(document_id)

    CATALOG_PATH.write_text(
        json.dumps(catalog, indent=4),
        encoding="utf-8"
    )

    print(f"\nTotal catalog documents: {len(catalog)}")


if __name__ == "__main__":
    generate_documents()

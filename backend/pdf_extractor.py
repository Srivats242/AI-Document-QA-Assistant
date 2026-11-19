import os
import re
from pathlib import Path

from text_cleaner import clean_extracted_text


def needs_ocr(text: str) -> bool:
    if not text.strip():
        return True

    # Look for patterns observed in PDFs with bad font mappings.
    corruption_patterns = [
        r"[A-Za-z],-[A-Za-z]",
        r"[A-Za-z]D,-[A-Za-z]",
        r"Cha\$t&r",
        r"5677689ar6&7",
    ]

    return any(
        re.search(pattern, text)
        for pattern in corruption_patterns
    )


def extract_page_text(page, use_ocr=True) -> str:
    text = page.get_text("text")

    if use_ocr and needs_ocr(text):
        tessdata_path = (
            os.getenv("TESSDATA_PREFIX")
            or r"C:\Program Files\Tesseract-OCR\tessdata"
        )

        if Path(tessdata_path).is_dir():
            try:
                ocr_page = page.get_textpage_ocr(
                    language="eng",
                    dpi=300,
                    full=True,
                    tessdata=tessdata_path,
                )

                ocr_text = page.get_text(
                    "text",
                    textpage=ocr_page,
                )

                if ocr_text.strip():
                    text = ocr_text

            except Exception as error:
                print(f"OCR failed: {error}")

    return clean_extracted_text(text)

---
name: pdf-merge
description: Merge multiple PDF files into a single PDF document. Use when the
user wants to combine, merge, concatenate, or join PDF files together into one
file.
---
# PDF Merge
Merge multiple PDFs into a single document using pypdf.

## Usage

```python
import logging

from pypdf import PdfReader, PdfWriter

# Suppress recoverable parser warnings from valid-but-imperfect source PDFs.
logging.getLogger("pypdf").setLevel(logging.ERROR)

writer = PdfWriter()
pdf_files = ["file1.pdf", "file2.pdf", "file3.pdf"]
for pdf_file in pdf_files:
    reader = PdfReader(pdf_file)
    for page in reader.pages:
        writer.add_page(page)

with open("merged.pdf", "wb") as output:
    writer.write(output)
```
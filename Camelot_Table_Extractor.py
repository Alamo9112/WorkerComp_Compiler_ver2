#!/usr/bin/env python3
"""
camelot_table_extractor.py

Standalone script to extract tables from a PDF using Camelot.

Before you run:
  1. Confirm your Python environment:
       python3 --version
       python3 -m pip --version
  2. Remove any conflicting package:
       python3 -m pip uninstall camelot
       # If you're using Conda:
       conda list | grep camelot
       conda remove camelot
  3. Install Camelot with OpenCV support:
       python3 -m pip install "camelot-py[cv]"
       # Or via Conda-forge:
       conda install -c conda-forge camelot-py
  4. Verify the correct module is found:
       python3 -c "import camelot; print('Loaded from:', getattr(camelot, '__file__', camelot.__path__))"
       python3 -c "python3 - << 'EOF'\nfrom camelot.io import read_pdf; print('read_pdf available at', read_pdf)\nEOF"

Usage:
  python3 camelot_table_extractor.py <PDF_PATH> [--flavor lattice|stream] [--pages PAGES]
      [--areas x1,y1,x2,y2 [...]] [--output-csv]

Example:
  python3 camelot_table_extractor.py WorkersData_Week7.pdf \
      --flavor lattice --pages all \
      --areas 50,100,500,700 --output-csv
"""
import sys
import argparse

# 1) Import the base module for debugging
try:
    import camelot
    location = getattr(camelot, '__file__', camelot.__path__)
    print(f"[DEBUG] camelot loaded from: {location}")
    print(f"[DEBUG] camelot contents: {dir(camelot)}")
except ImportError:
    sys.exit(
        "Error: 'camelot' module not found in this environment.\n"
        "Ensure you installed the correct package: python3 -m pip install 'camelot-py[cv]'"
    )

# 2) Import read_pdf directly
try:
    from camelot.io import read_pdf
    print(f"[DEBUG] read_pdf imported successfully: {read_pdf}")
except ImportError:
    sys.exit(
        "Error: Could not import read_pdf from camelot.io.\n"
        "This usually means a conflicting 'camelot' package is installed.\n"
        "Remove it and reinstall: python3 -m pip uninstall camelot && python3 -m pip install 'camelot-py[cv]'"
    )


def extract_tables(pdf_path, flavor='lattice', pages='all', table_areas=None, output_csv=False):
    """
    Extract tables from a PDF using camelot.io.read_pdf.
    Retries in stream mode if lattice mode finds nothing.

    Args:
        pdf_path (str): path to PDF.
        flavor (str): 'lattice' or 'stream'.
        pages (str): pages to parse.
        table_areas (list): optional list of 'x1,y1,x2,y2'.
        output_csv (bool): if True, save each table as CSV.
    """
    options = {'flavor': flavor, 'pages': pages}
    if table_areas:
        options['table_areas'] = table_areas

    print(f"Extracting tables from {pdf_path} (flavor={flavor}, pages={pages})...")
    try:
        tables = read_pdf(pdf_path, **options)
    except Exception as e:
        sys.exit(f"Error reading PDF: {e}")

    # Fallback: lattice -> stream if no tables found
    n = getattr(tables, 'n', len(tables))
    if n == 0 and flavor == 'lattice':
        print("No tables found in lattice mode — retrying with stream mode...")
        return extract_tables(pdf_path, flavor='stream', pages=pages,
                              table_areas=table_areas, output_csv=output_csv)

    print(f"Found {n} table(s) using {flavor} mode.")
    for i, table in enumerate(tables, start=1):
        print(f"\n-- Table {i} --")
        df = table.df
        print(df)
        if output_csv:
            csv_name = f"table_{i}_{flavor}.csv"
            table.to_csv(csv_name)
            print(f"Saved CSV: {csv_name}")
    return tables


def main():
    parser = argparse.ArgumentParser(
        description='Extract tables from a PDF using Camelot.'
    )
    parser.add_argument('pdf', help='Path to the PDF file')
    parser.add_argument('-f', '--flavor', choices=['lattice', 'stream'], default='lattice',
                        help="Extraction mode: 'lattice' (grid lines) or 'stream' (whitespace)")
    parser.add_argument('-p', '--pages', default='all',
                        help="Pages to parse (e.g. '1,2-3' or 'all')")
    parser.add_argument('-a', '--areas', nargs='+',
                        metavar='x1,y1,x2,y2',
                        help="Optional: restrict extraction to these regions")
    parser.add_argument('-o', '--output-csv', action='store_true',
                        help='Save each extracted table as CSV')
    args = parser.parse_args()

    extract_tables(
        pdf_path=args.pdf,
        flavor=args.flavor,
        pages=args.pages,
        table_areas=args.areas,
        output_csv=args.output_csv
    )


if __name__ == '__main__':
    main()

import zipfile
import logging
from io import StringIO
import pandas as pd

def merge(z : zipfile.ZipFile, reports_fns : list[str]):
    dfs = []
    completed = []
    warnings = []
    errors = []
    for fn in reports_fns:
        logging.info(f'Processing report file {fn}')
        try:
            with z.open(fn) as rf:
                report_raw = rf.read().decode()
            
                logging.info(f'Report length: {len(report_raw)} chars')

                if '|' in report_raw:
                    logging.warning(f'Warning: feedback narrative {fn} contains separator character "|" (why?!). Deleting this character.')
                    report_raw = report_raw.replace('|', "")
                    warnings.append(fn)

                rf = report_raw.splitlines(False)
                header = rf[0]
                header = header.replace(',','|')
                lines = [header]
                for line in rf[1:]:
                    line = line.strip()[1:-1]
                    lines.append(line.replace('","', "|"))
            report = '\n'.join(lines)
            df = pd.read_csv(StringIO(report), delimiter='|')
            dfs.append(df)
            completed.append(fn)

        except Exception as e:
            logging.error(f'Failed to process report {fn}! Error was:\n{e}')
            errors.append(fn)

    return dfs, completed, warnings, errors
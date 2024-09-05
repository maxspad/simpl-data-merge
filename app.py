import streamlit as st
import zipfile
import pandas as pd
from io import StringIO
import logging 

# Set up logging
logFormatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
rootLogger = logging.getLogger()
rootLogger.setLevel(logging.DEBUG)

if not len(rootLogger.handlers):
    # only if this is our first run
    fileHandler = logging.FileHandler('test.log.txt', mode='w')
    fileHandler.setFormatter(logFormatter)
    rootLogger.addHandler(fileHandler)

    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    rootLogger.addHandler(consoleHandler)

f = st.file_uploader('Upload ZIP file here')#, type=['zip'])

if f is None:
    st.warning('Please upload a file to continue.')
    logging.error('No file uploaded. Stopping.')
    st.stop()

# check to make sure it's actually a zip file
if not zipfile.is_zipfile(f):
    st.error(f'{f.name} is not a valid ZIP. Please upload a valid ZIP file.')
    logging.error(f'{f.name} is not a valid ZIP!')
    st.stop()

# Open the file and get the list of files inside
z = zipfile.ZipFile(f)
zfiles = z.namelist()

user_reports = [fn for fn in zfiles if 'user_report' in fn]
mile_reports = [fn for fn in zfiles if 'milestone_report' in fn]

if len(user_reports) + len(mile_reports) == 0:
    # we have no matching files
    st.error('No user reports or milestone reports found. Is this the right ZIP file?')
    logging.error('No user reports or milestone reports found. Stopping.')
    st.stop()

if not len(user_reports):
    st.warning('No user reports found, skipping user report merge.')
    logging.warning('No user reports found, skipping user report merge.')

if not len(mile_reports):
    st.warning('No milestone reports found. Skipping milestone report merge.')
    logging.warning('No milestone reports found. Skipping milestone report merge.')

dfs = []
completed = []
warnings = []
errors = []
for fn in user_reports:
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

if len(errors):
    logging.error('There were errors during merge.')
    st.error('There were errors during merge. Please check the logs.')

if not len(dfs):
    logging.error('No dataframes available to merge, did they all error out?')
    st.stop()

try:
    df = pd.concat(dfs, axis=0)
except Exception as e:
    logging.error(f'Error combining dataframes. Error was:\n{e}')
    st.error('There was an error during the final merge step. There may be formatting errors in the individual reports. Please check the logs')
    st.stop()


data_csv = df.to_csv(index=False)
st.write(f'Merge complete. **Completed**: {len(completed)} **Warnings**: {len(warnings)} **Errors**: {len(errors)}')
logging.info(f'Merge complete. Df shape: {df.shape}')

st.write('Merged data:')
st.dataframe(df)


@st.fragment
def download_button_fragment():
    st.download_button('Click to download merged data.', data_csv, file_name='reports_merged.csv')

download_button_fragment()



    
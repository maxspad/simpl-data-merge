import streamlit as st
import zipfile
import pandas as pd
from io import StringIO
import logging 
import merge

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


st.title('SIMPL Report Merging Tool')

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

def run_reports(reps, report_type):
    dfs, completed, warnings, errors = merge.merge(z, reps)

    if len(errors):
        logging.error('There were errors during merge.')
        st.error('There were errors during merge. Please check the logs.')        

    if not len(dfs):
        logging.error('No dataframes available to merge, did they all error out?')
        return None
    
    try: 
        df = pd.concat(dfs, axis=0)
    except Exception as e:
        logging.error(f'Error combining dataframes. Error was:\n{e}')
        st.error('There were errors during the final merge step. Please check the logs')
        return None
    
    data_csv = df.to_csv(index=False)
    st.write(f'Merge complete. **Completed**: {len(completed)} **Warnings**: {len(warnings)} **Errors**: {len(errors)}')
    logging.info(f'Merge complete. Df shape: {df.shape}')

    st.download_button('Click here to download merged data',
                       data_csv,
                       file_name=f'simpl-merged-{report_type}.csv',
                       mime='text/csv')
    st.write('**Merged data:**')
    st.dataframe(df)

st.header('User Reports')
if len(user_reports):
    run_reports(user_reports, 'user-reports')
else:
    st.warning('No user reports found in ZIP. Skipping user report merge.')
    logging.warning('No user reports found, skipping user report merge.')

st.header('Milestone Reports')
if len(mile_reports):
    run_reports(mile_reports, 'milestone-reports')
else:
    st.warning('No milestone reports found in ZIP. Skipping milestone report merge.')
    logging.warning('No milestone reports found. Skipping milestone report merge.')

st.divider()
with open('test.log.txt', 'r') as f:
    st.download_button('Download Logs', f)

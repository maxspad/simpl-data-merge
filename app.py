import streamlit as st
import zipfile
import pandas as pd
from io import StringIO
import logging 
import merge
import sys

_LOG_FILE_NAME = 'simpl-merge-log.txt'

st.set_page_config(page_title='SIMPL Merge Utility')

# Set up logging
logFormatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
rootLogger = logging.getLogger()
rootLogger.setLevel(logging.DEBUG)

# pyodide has its own logger registered
if (not len(rootLogger.handlers)) or ('pyodide' in sys.modules):
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    rootLogger.addHandler(consoleHandler)

st.title('SIMPL Report Merging Tool')
st.markdown('''
This is a small utility that merges all of the individual user reports within
the bulk report ZIP file produced by the SIMPL dashboard. Upload the ZIP file
below and it will be automatically processed. SIMPL user reports and milestone reports
are processed separately. 
         
*Privacy Note*: Although this utility is served via a webpage, all data processing 
happens locally on *your* computer. The "upload" button below does not actually send any 
data from your computer. For more information, see [this link](https://pyodide.org/en/stable/).
''')

def run_reports(reps, report_title, report_type):
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
        logging.exception(f'Error combining dataframes. Error was:\n{e}')
        st.error('There were errors during the final merge step. Please check the logs')
        return None
    
    data_csv = df.to_csv(index=False)
    st.write(f'{report_title} merge complete. **Completed**: {len(completed)} **Warnings**: {len(warnings)} **Errors**: {len(errors)}')
    logging.info(f'{report_title} merge complete. Df shape: {df.shape}')

    st.download_button(f'Download Merged {report_title}',
                       data_csv,
                       file_name=f'simpl-merged-{report_type}.csv',
                       mime='text/csv')
    with st.expander(f'**Preview merged {report_title}:**'):
        st.dataframe(df)
    
zf = st.file_uploader('Upload ZIP file here', type=['zip'])

placeholder = st.container()

st.divider()
st.markdown("Problems? Email Max.")
st.caption("©️ Max Spadafore 2024. This is an open source utility available under the MIT license. Code is available [here](https://github.com/maxspad/simpl-data-merge)")

with placeholder:
    if zf is None:
        st.warning('Please upload a file to continue.')
        logging.error('No file uploaded. Stopping.')
        st.stop()

    # check to make sure it's actually a zip file
    if not zipfile.is_zipfile(zf):
        st.error(f'{zf.name} is not a valid ZIP. Please upload a valid ZIP file.')
        logging.error(f'{zf.name} is not a valid ZIP!')
        st.stop()

    # Open the file and get the list of files inside
    z = zipfile.ZipFile(zf)
    zfiles = z.namelist()

    user_reports = [fn for fn in zfiles if 'user_report' in fn]
    mile_reports = [fn for fn in zfiles if 'milestone_report' in fn]

    if len(user_reports) + len(mile_reports) == 0:
        # we have no matching files
        st.error('No user reports or milestone reports found. Is this the right ZIP file?')
        logging.error('No user reports or milestone reports found. Stopping.')
        st.stop()

    t1, t2 = st.tabs(['User Reports','Milestone Reports'])
    with t1:
        # st.header('User Reports')
        if len(user_reports):
            run_reports(user_reports, 'User Reports', 'user-reports')
        else:
            st.warning('No user reports found in ZIP. Skipping user report merge.')
            logging.warning('No user reports found, skipping user report merge.')
    with t2: 
        # st.header('Milestone Reports')
        if len(mile_reports):
            run_reports(mile_reports, 'Milestone Reports', 'milestone-reports')
        else:
            st.warning('No milestone reports found in ZIP. Skipping milestone report merge.')
            logging.warning('No milestone reports found. Skipping milestone report merge.')
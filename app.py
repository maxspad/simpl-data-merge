import streamlit as st
import zipfile
import pandas as pd
from io import StringIO
from csv import QUOTE_ALL
import re

f = st.file_uploader('Upload ZIP file here')#, type=['zip'])

if f is None:
    st.warning('Please upload a file to continue.')
    st.stop()

# check to make sure it's actually a zip file
if not zipfile.is_zipfile(f):
    st.error(f'{f.name} is not a valid ZIP. Please upload a valid ZIP file.')
    st.stop()


# Open the file and get the list of files inside
z = zipfile.ZipFile(f)
zfiles = z.namelist()

user_reports = [fn for fn in zfiles if 'user_report' in fn]
mile_reports = [fn for fn in zfiles if 'milestone_report' in fn]

if len(user_reports) + len(mile_reports) == 0:
    # we have no matching files
    st.error('No user reports or milestone reports found. Is this the right ZIP file?')
    st.stop()

if not len(user_reports):
    st.warning('No user reports found, skipping user report merge.')

if not len(mile_reports):
    st.warning('No milestone reports found. Skipping milestone report merge.')

dfs = []
for fn in user_reports:
    # st.write(fn)
    with z.open(fn) as rf:
        report_raw = rf.read().decode()
        if '|' in report_raw:
            st.warning(f'Warning: feedback narrative {fn} contains separator character "|" (why?!). Deleting this character.')
            report_raw = report_raw.replace('|', "")

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

df = pd.concat(dfs, axis=0)
st.dataframe(df)
    

    
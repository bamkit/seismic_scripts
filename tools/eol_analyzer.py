import pandas as pd
from sqlalchemy import create_engine, Column, Integer, Float, String, MetaData, Table, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import re
import os


# Dynamically create DetailTable with columns from combined_df
def create_detail_table(metadata, combined_df):
    # Define the DetailTable dynamically
    columns = [
        Column("id", Integer, primary_key=True),
        Column("line_id", Integer, ForeignKey('sequence_table.id'))
    ]

    df_columns = combined_df.columns()

    # Loop through combined_df's columns
    for col in df_columns:
        # Define column type based on the DataFrame's dtype
        dtype = combined_df[col].dtype
        if dtype.kind in {'i', 'u'}:  # Integer columns
            columns.append(Column(col, Integer))
        elif dtype.kind == 'f':  # Float columns
            columns.append(Column(col, Float))
        else:  # Default to String for other types
            columns.append(Column(col, String))

    # Create a new table dynamically
    return Table('detail_table', metadata, *columns)

def parse_eol_sections(file_path: str) -> dict:

    sections = {}
    current_section = None
    current_headers = None
    current_data = []

    with open(file_path, 'r') as f:
        # Skip first line (EOL_Report)
        next(f)

        # Skip initial empty line if present
        line = next(f).strip()
        if not line:
            line = next(f).strip()

        while True:
            try:
                # New section starts with title
                if current_section is None:
                    current_section = line

                    # Skip empty line after title
                    next(f)

                    # Get headers
                    current_headers = next(f).strip().split(',')

                    # Skip empty line after headers
                    next(f)

                    # Start reading data
                    line = next(f).strip()
                    current_data = []
                    continue

                # Empty line marks end of current section
                if not line:
                    # Convert collected data to DataFrame
                    df = pd.DataFrame(current_data, columns=current_headers)

                    # Convert Time column to datetime if it exists
                    if 'Time' in df.columns:
                        df['Time'] = pd.to_datetime(df['Time'], format='%d/%m/%Y %H:%M:%S')

                    sections[current_section] = df
                    current_section = None
                    current_data = []
                    line = next(f).strip()
                    continue

                # Add data row to current section
                current_data.append(line.split(','))
                line = next(f).strip()

            except StopIteration:
                # Convert last section if exists
                if current_section and current_data:
                    df = pd.DataFrame(current_data, columns=current_headers)
                    if 'Time' in df.columns:
                        df['Time'] = pd.to_datetime(df['Time'], format='%d/%m/%Y %H:%M:%S')
                    sections[current_section] = df
                break

        combined_df = None

        for key, df in sections.items():
            if combined_df is None:
                combined_df = df
            else:
                combined_df = pd.merge(combined_df, df, on=["Shot #", "Time"], how="outer")

        # Fill NaN if needed, e.g., with 0 or a placeholder value
        combined_df = combined_df.fillna(0)

    return combined_df

def make_columns_sql_ready(df):
    def clean_column_name(col):
        # Replace spaces with underscores
        col = col.replace(" ", "_")
        # Remove special characters (retain alphanumeric and underscores)
        col = re.sub(r'\W', '', col)
        # Ensure the column name starts with a letter
        if re.match(r'^\d', col):
            col = f"col_{col}"  # Prefix with 'col_' if it starts with a digit
        # Handle reserved SQL keywords (optional: add more keywords as needed)
        reserved_keywords = {"SELECT", "FROM", "WHERE", "TABLE"}
        if col.upper() in reserved_keywords:
            col = f"{col}_col"  # Append '_col' to reserved keywords
        return col

    # Apply cleaning to all columns
    df.columns = [clean_column_name(col) for col in df.columns]
    return df

def find_files(start_seq, end_seq, root_dir):

    production_lines = list()
    # Iterate through the range of folder names
    for i in range(start_seq, end_seq):
        folder_name = f'Seq{i}'
        folder_path = os.path.join(root_dir, folder_name)

        if os.path.isdir(folder_path):  # Check if the folder exists
            pp_sp_path = os.path.join(folder_path, 'PP_SP_Range')
            if os.path.isdir(pp_sp_path):
                # print(pp_sp_path)
                for dirpath, dirnames, filenames in os.walk(pp_sp_path):
                    for filename in filenames:
                        if filename.endswith('-EOL_Report.csv'):
                            file_path = os.path.join(dirpath, filename)
                            if file_path[-29] not in ['7']:
                                production_lines.append(file_path)
                                # print(file_path)

    return production_lines


# Usage example
if __name__ == '__main__':

    start = 1001
    end = 1081
    database_url = "sqlite:///eol_report.db"
    folder_path = r"Z:\MT3007424\Murphy_KMS_3D_OBN\00_NAV"
    eol_file = r"Z:\MT3007424\Murphy_KMS_3D_OBN\00_NAV\Seq1061\PP_SP_Range\5331111061-EOL_Report.csv"

    # Define the base class
    Base = declarative_base()


    class SequenceTable(Base):
        __tablename__ = 'sequence_table'
        id = Column(Integer, primary_key=True)
        linename = Column(String)
        preplot = Column(Integer)
        sequence = Column(Integer)
        type = Column(String)
        pass_field = Column(Integer)  # 'pass' is a reserved keyword
        fgsp = Column(Integer)
        fgsp_time = Column(String)  # Use DateTime for actual timestamps
        lgsp = Column(Integer)
        lgsp_time = Column(String)
        direction = Column(String)
        length = Column(Float)
        details = relationship("DetailTable", back_populates="main")


    # Set up the database connection
    engine = create_engine('sqlite:///example.db')  # Replace with your database URI
    Base.metadata.create_all(engine)  # Create the tables in the database
    Session = sessionmaker(bind=engine)
    session = Session()

    eol_files = find_files(start, end, folder_path)

    # Create details table

    df = parse_eol_sections(eol_files[0])




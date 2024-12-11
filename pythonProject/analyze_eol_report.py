import pandas as pd
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, Float, String, DateTime, ForeignKey
# from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
import os
from pathlib import Path
import re

Base = declarative_base()

class EOLFile(Base):
    """Stores information about each EOL file processed"""
    __tablename__ = 'eol_files'
    
    id = Column(Integer, primary_key=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(1000))
    processed_date = Column(DateTime, default=datetime.datetime.utcnow)
    line_name = Column(String(100))
    vessel_name = Column(String(100))
    survey_name = Column(String(100))
    
class NetworkQuality(Base):
    """Network Quality measurements"""
    __tablename__ = 'network_quality'
    
    id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey('eol_files.id'))
    shot_number = Column(Integer)
    timestamp = Column(DateTime)
    main_dof = Column(Float)
    main_quality = Column(Float)

class ShotPointInterval(Base):
    """Shot Point Interval measurements"""
    __tablename__ = 'shot_point_interval'
    
    id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey('eol_files.id'))
    shot_number = Column(Integer)
    timestamp = Column(DateTime)
    shot_point_spacing = Column(Float)
    shot_point_interval = Column(Float)

class GPSPosition(Base):
    """GPS Position measurements"""
    __tablename__ = 'gps_position'
    
    id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey('eol_files.id'))
    shot_number = Column(Integer)
    timestamp = Column(DateTime)
    latitude = Column(Float)
    longitude = Column(Float)
    easting = Column(Float)
    northing = Column(Float)
    quality = Column(Float)

class VesselMetrics(Base):
    """Vessel speed and other metrics"""
    __tablename__ = 'vessel_metrics'
    
    id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey('eol_files.id'))
    shot_number = Column(Integer)
    timestamp = Column(DateTime)
    speed = Column(Float)
    heading = Column(Float)
    water_depth = Column(Float)

def init_database(database_url: str):
    """Initialize the database with all tables"""
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    return engine

def process_eol_file(file_path: str, engine, session):
    """Process a single EOL file and store in database"""
    # Parse file using existing parse_eol_sections function
    sections = parse_eol_sections(file_path)
    
    # Create file record
    file_record = EOLFile(
        filename=os.path.basename(file_path),
        file_path=file_path,
        # You might want to extract these from the file content
        line_name="Line1",
        vessel_name="Vessel1",
        survey_name="Survey1"
    )
    session.add(file_record)
    session.flush()  # Get the file_id
    
    # Process each section
    for section_name, df in sections.items():
        if section_name == "Network Quality":
            for _, row in df.iterrows():
                record = NetworkQuality(
                    file_id=file_record.id,
                    shot_number=row['Shot #'],
                    timestamp=row['Time'],
                    main_dof=row.get('main DOF'),
                    main_quality=row.get('main Quality')
                )
                session.add(record)
                
        elif section_name == "Shot Point Interval":
            for _, row in df.iterrows():
                record = ShotPointInterval(
                    file_id=file_record.id,
                    shot_number=row['Shot #'],
                    timestamp=row['Time'],
                    shot_point_spacing=row.get('V1 Shot Point Spacing m'),
                    shot_point_interval=row.get('Shot Point Interval s')
                )
                session.add(record)
        
        # Add similar processing for other sections
        
    session.commit()

def process_multiple_files(folder_path: str, database_url: str):
    """Process multiple EOL files"""
    engine = init_database(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        for file_path in Path(folder_path).glob('*EOL_Report*.csv'):
            print(f"Processing {file_path.name}")
            process_eol_file(str(file_path), engine, session)
            
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

# Example queries
def get_example_queries(engine):
    """Example queries to demonstrate database usage"""
    
    # Get all network quality measurements for a specific file
    query1 = """
    SELECT f.filename, nq.*
    FROM network_quality nq
    JOIN eol_files f ON nq.file_id = f.id
    WHERE f.filename = :filename
    """
    
    # Get average shot point intervals by file
    query2 = """
    SELECT f.filename, 
           AVG(spi.shot_point_spacing) as avg_spacing,
           COUNT(*) as shot_count
    FROM shot_point_interval spi
    JOIN eol_files f ON spi.file_id = f.id
    GROUP BY f.filename
    """
    
    # Get vessel metrics where speed was outside normal range
    query3 = """
    SELECT f.filename, vm.*
    FROM vessel_metrics vm
    JOIN eol_files f ON vm.file_id = f.id
    WHERE vm.speed > 5.0 OR vm.speed < 3.0
    ORDER BY vm.timestamp
    """
    
    return {
        "network_quality": pd.read_sql_query(query1, engine, params={"filename": "example.csv"}),
        "shot_point_stats": pd.read_sql_query(query2, engine),
        "abnormal_speed": pd.read_sql_query(query3, engine)
    }

def parse_eol_sections(file_path: str) -> dict:
    """
    Parse EOL Report file into sections and convert to pandas DataFrames.
    Converts 'Time' columns to datetime objects.
    
    Args:
        file_path (str): Path to the EOL report file
        
    Returns:
        dict: Dictionary with section titles as keys containing pandas DataFrames
    """
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
                
    return sections


def clean_table_name(name: str) -> str:
    """
    Clean section name to make it SQL-friendly
    Removes special characters and spaces, converts to lowercase
    """
    # Replace spaces and special chars with underscore
    clean = re.sub(r'[^a-zA-Z0-9]', '_', name)
    # Remove multiple consecutive underscores
    clean = re.sub(r'_+', '_', clean)
    # Remove leading/trailing underscores
    clean = clean.strip('_').lower()
    return clean

def save_sections_to_sql(sections: dict, database_url: str, if_exists: str = 'replace'):
    """
    Save each section DataFrame to a separate SQL table
    
    Args:
        sections (dict): Dictionary of DataFrames from parse_eol_sections
        database_url (str): SQLAlchemy database URL
        if_exists (str): How to behave if table exists ('fail', 'replace', or 'append')
    """
    # Create SQLAlchemy engine
    engine = create_engine(database_url)
    
    # Store each DataFrame as a table
    for section_name, df in sections.items():
        # Clean the section name to make it SQL-friendly
        table_name = clean_table_name(section_name)
        
        # Save to SQL
        df.to_sql(
            name=table_name,
            con=engine,
            if_exists=if_exists,
            index=False
        )
        
        print(f"Saved table: {table_name} ({len(df)} rows)")

        
def process_multiple_files(folder_path: str, database_url: str):
    """
    Process multiple EOL files, skipping files that have already been processed
    """
    engine = init_database(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Get list of already processed files
        existing_files = set(
            session.query(EOLFile.filename).all()
        )
        existing_files = {file[0] for file in existing_files}  # Convert to set of filenames
        
        # Process each file in the folder
        for file_path in Path(folder_path).glob('[0-9]'*10 + '-EOL_Report*.csv'):
            filename = file_path.name
            
            # Skip if file was already processed
            if filename in existing_files:
                print(f"Skipping {filename} - already processed")
                continue
                
            print(f"Processing new file: {filename}")
            process_eol_file(str(file_path), engine, session)
            
    except Exception as e:
        session.rollback()
        print(f"Error processing files: {str(e)}")
        raise e
    finally:
        session.close()

# Optional: Add a function to show processing status
def show_processing_status(database_url: str):
    """Show statistics about processed files"""
    engine = create_engine(database_url)
    
    try:
        # Get file counts
        with engine.connect() as conn:
            # First check if tables exist
            metadata = MetaData()
            metadata.reflect(bind=engine)
            
            print("\nProcessing Status:")
            
            # Check eol_files table
            if 'eol_files' in metadata.tables:
                total_files = pd.read_sql_query(
                    "SELECT COUNT(*) as count FROM eol_files", 
                    conn
                ).iloc[0]['count']
                print(f"Total files processed: {total_files}")
            else:
                print("No files processed yet (eol_files table doesn't exist)")
                return
            
            # Get counts per table
            print("\nFiles with data in each table:")
            tables = ['network_quality', 'shot_point_interval', 'gps_position', 'vessel_metrics']
            
            for table in tables:
                if table in metadata.tables:
                    try:
                        count = pd.read_sql_query(
                            f"""
                            SELECT COUNT(*) as count 
                            FROM {table}
                            """,
                            conn
                        ).iloc[0]['count']
                        print(f"{table}: {count} records")
                    except Exception as e:
                        print(f"{table}: Error getting count - {str(e)}")
                else:
                    print(f"{table}: Table not created yet")
    
    except Exception as e:
        print(f"Error checking status: {str(e)}")

# Usage example
if __name__ == '__main__':
    database_url = "sqlite:///eol_report.db"
    folder_path = r"Z:\MT3007424\Murphy_KMS_3D_OBN\00_NAV"
    
    # Process files
    process_multiple_files(folder_path, database_url)
    
    # Show processing status
    show_processing_status(database_url)


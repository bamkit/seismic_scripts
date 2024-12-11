import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog
from PyQt5.uic import loadUi
import pandas as pd
from datetime import datetime
import os


class MyBoobies(QMainWindow):
    def __init__(self):
        super(MyBoobies, self).__init__()
        loadUi('mainwindow.ui', self)  # Load the .ui file created in Qt Designer
        self.setWindowTitle("TSDIP PARSER")

        # Connect the "Load File" button to open file dialog
        self.load_file_button.clicked.connect(self.open_file_dialog)

        # Connect the "Parse File" button to parse the loaded file
        self.parse_file_button.clicked.connect(self.parse_and_save_file)

        # Connect the "Exit" button to the close function
        self.exit_button.clicked.connect(self.close_application)

        # Initialize file type selector
        self.file_type_selector.addItems(["HD46.pro", "Dive.000", "HSS_SVP.csv"])

        self.file_path = None
        self.tsdip_df = None
        self.svp_format_df = None
        self.tsdip_out = None
        self.current_datetime = None
        self.svp_name = None
        self.orca_format = None
        self.loaded_file_content = None

    @staticmethod
    def parse_tsdip(tsdip):

        df = pd.read_csv(tsdip, sep='\t', skiprows=27)
        df = df.drop(columns=['Unnamed: 8'])
        return df

    @staticmethod
    def parse_tsdip_havila(tsdip):

        colnames = ['Depth', 'Sound Velocity', 'Temperature', 'Salinity']
        df = pd.read_csv(tsdip, sep='\t', skiprows=6, names=colnames)

        return df

    @staticmethod
    def parse_tsdip_hss(tsdip):

        # colnames = ['Depth', 'Sval Measured', 'Temperature', 'Salinity', 'Density', 'Sound Velocity', 'e1', 'e2', 'e3']
        df_raw = pd.read_csv(tsdip, skiprows=1, encoding='ISO-8859-1')
        print(df_raw.columns)
        df = df_raw[['Depth (Meter)', 'Sound Velocity: Calculated (m/s)', 'Temperature (°C)', 'Salinity (PSU)']].copy()

        print(df.head())

        return df

    @staticmethod
    def tsdip_to_svp_format(df):

        svp_df = df[['PRESSURE;DBAR', 'Calc. SOUND VELOCITY;M/SEC', 'TEMPERATURE;C', 'Calc. SALINITY;']].copy()

        return svp_df

    def open_file_dialog(self):
        options = QFileDialog.Options()
        self.file_path, _ = QFileDialog.getOpenFileName(
                                                    self,
                                                    "Open File",
                                                    "~",
                                                    "Text Files (*.txt);;All Files (*)",
                                                    options=options
                                                    )
        if self.file_path:
            with open(self.file_path, 'r') as file:
                self.loaded_file_content = file.read()
            self.file_path_label.setText("File Path: " + self.file_path)
            self.file_content_browser.setPlainText(self.loaded_file_content)

    def parse_and_save_file(self):

        tsdip_header1 = list()

        lat = self.lat_input.text()
        lon = self.lon_input.text()
        date = self.date_input.text()
        t = self.time_input.text()

        tsdip_header1.append(f'Latitude\t"{lat}"\n')
        tsdip_header1.append(f'Longitude\t"{lon}"\n')
        tsdip_header1.append(f'Date\t{date}\n')
        tsdip_header1.append(f'Time\t{t}\n')
        tsdip_header1.append(f'Description\tValeport SVX2 #40710\t\t\n')

        if self.loaded_file_content:
            file_type = self.file_type_selector.currentText()
            if file_type == "Dive.000":
                self.tsdip_df = self.parse_tsdip(self.file_path)
                self.svp_format_df = self.tsdip_to_svp_format(self.tsdip_df)
            elif file_type == "HD46.pro":
                self.svp_format_df = self.parse_tsdip_havila(self.file_path)
            elif file_type == "HSS_SVP.csv":
                self.svp_format_df = self.parse_tsdip_hss(self.file_path)

            print(self.svp_format_df.head(0))
            # Folder location of the raw tsdip file
            self.tsdip_out = os.path.dirname(self.file_path)

            # Current date to append to file name
            self.current_datetime = datetime.now().strftime("%Y-%m-%d")

            self.svp_name = os.path.join(self.tsdip_out, 'tdsip_' + self.current_datetime + '.svp')

            # file name of tsdip to be imported to orca
            self.orca_format = os.path.join(self.tsdip_out, 'orcatsdip_' + self.current_datetime + '.svp')

            self.svp_format_df.to_csv(self.svp_name, sep='\t', index=False, header=None)

            with open(self.svp_name, 'r') as f:
                f_readlines = f.readlines()
                orca_tsdip = tsdip_header1 + f_readlines

            with open(self.orca_format, 'w') as f:
                f.writelines(orca_tsdip)

            os.remove(self.svp_name)
            os.startfile(self.orca_format)

        else:
            self.svp_output_label.setText("No file loaded.")

    def close_application(self):
        self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyBoobies()
    window.show()
    sys.exit(app.exec_())


import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Dict, Tuple

class VesselDataAnalyzer:
    def __init__(self, root_folder: str, output_folder: str):
        self.root_folder = root_folder
        self.output_folder = output_folder
        os.makedirs(output_folder, exist_ok=True)
        
    def extract_section_data(self, lines: List[str], start_marker: str, end_marker: str) -> Tuple[List[str], int]:
        """Extract data between markers and return the section with its start index"""
        try:
            start_idx = next(i for i, line in enumerate(lines) if start_marker in line)
            end_idx = next(i for i, line in enumerate(lines[start_idx:]) if end_marker in line)
            return lines[start_idx:start_idx + end_idx], start_idx
        except StopIteration:
            return [], -1

    def process_crab_angle_data(self, lines: List[str], line_name: str) -> pd.DataFrame:
        """Process crab angle data and create visualization"""
        section_data, _ = self.extract_section_data(lines, "Vessel CMG and Crab Angle", "Gyro Headings")
        if not section_data:
            return None

        # Process data
        data = []
        for line in section_data[2:]:  # Skip header rows
            try:
                parts = line.strip().split(',')
                if len(parts) >= 3:
                    data.append({
                        'Shot': int(parts[0]),
                        'Time': parts[1],
                        'CMG': float(parts[2]),
                        'Crab_Angle': float(parts[-1])
                    })
            except (ValueError, IndexError):
                continue

        if not data:
            return None

        df = pd.DataFrame(data)
        
        # Create plot
        plt.figure(figsize=(15, 8))
        
        # Plot crab angle
        plt.plot(df['Shot'], df['Crab_Angle'], label='Crab Angle')
        
        # Calculate and plot statistics
        avg_angle = df['Crab_Angle'].mean()
        max_angle = df['Crab_Angle'].max()
        min_angle = df['Crab_Angle'].min()
        avg_cmg = df['CMG'].mean()
        
        plt.axhline(y=avg_angle, color='r', linestyle='--', label=f'Average: {avg_angle:.2f}°')
        plt.axhline(y=max_angle, color='g', linestyle=':', label=f'Max: {max_angle:.2f}°')
        plt.axhline(y=min_angle, color='y', linestyle=':', label=f'Min: {min_angle:.2f}°')
        
        # Determine line direction
        line_direction = "0°" if 270 <= avg_cmg <= 360 or 0 <= avg_cmg <= 90 else "180°"
        
        plt.title(f'Line {line_name}: Crab Angle vs Shot Number (Line Direction: {line_direction})')
        plt.xlabel('Shot Number')
        plt.ylabel('Crab Angle (degrees)')
        plt.grid(True)
        plt.legend()
        
        # Add statistics text box
        stats_text = (f'Statistics:\n'
                     f'Shots: {len(df)}\n'
                     f'Average: {avg_angle:.2f}°\n'
                     f'Maximum: {max_angle:.2f}°\n'
                     f'Minimum: {min_angle:.2f}°\n'
                     f'Avg CMG: {avg_cmg:.2f}°')
        
        plt.text(0.02, 0.98, stats_text,
                transform=plt.gca().transAxes,
                verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Save plot
        plt.savefig(
            os.path.join(self.output_folder, f'{line_name}_crab_angle.png'),
            dpi=300,
            bbox_inches='tight'
        )
        plt.close()
        
        return df

    def process_gyro_data(self, lines: List[str], line_name: str) -> pd.DataFrame:
        """Process gyro heading data and create visualization"""
        section_data, _ = self.extract_section_data(lines, "Gyro Headings", "Network Quality")
        if not section_data:
            return None

        # Process data
        data = []
        for line in section_data[2:]:  # Skip header rows
            try:
                parts = line.strip().split(',')
                if len(parts) >= 3:
                    data.append({
                        'Shot': int(parts[0]),
                        'Time': parts[1],
                        'Gyro': float(parts[-1])
                    })
            except (ValueError, IndexError):
                continue

        if not data:
            return None

        df = pd.DataFrame(data)
        
        # Create plot
        plt.figure(figsize=(15, 8))
        
        # Plot gyro heading
        plt.plot(df['Shot'], df['Gyro'], label='Gyro Heading')
        
        # Calculate and plot statistics
        avg_gyro = df['Gyro'].mean()
        max_gyro = df['Gyro'].max()
        min_gyro = df['Gyro'].min()
        
        plt.axhline(y=avg_gyro, color='r', linestyle='--', label=f'Average: {avg_gyro:.2f}°')
        
        plt.title(f'Line {line_name}: Gyro Heading vs Shot Number')
        plt.xlabel('Shot Number')
        plt.ylabel('Gyro Heading (degrees)')
        plt.grid(True)
        plt.legend()
        
        # Add statistics text box
        stats_text = (f'Statistics:\n'
                     f'Shots: {len(df)}\n'
                     f'Average: {avg_gyro:.2f}°\n'
                     f'Maximum: {max_gyro:.2f}°\n'
                     f'Minimum: {min_gyro:.2f}°')
        
        plt.text(0.02, 0.98, stats_text,
                transform=plt.gca().transAxes,
                verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Save plot
        plt.savefig(
            os.path.join(self.output_folder, f'{line_name}_gyro_heading.png'),
            dpi=300,
            bbox_inches='tight'
        )
        plt.close()
        
        return df

    def process_file(self, file_path: str) -> None:
        """Process a single EOL report file"""
        try:
            # Read file
            with open(file_path, 'r') as file:
                lines = file.readlines()
                
            # Get line name from filename
            line_name = os.path.basename(file_path).replace('-EOL_Report.csv', '')
            
            # Process crab angle and gyro data
            crab_df = self.process_crab_angle_data(lines, line_name)
            gyro_df = self.process_gyro_data(lines, line_name)
            
            print(f"Processed: {line_name}")
            
        except Exception as e:
            print(f"Error processing file {file_path}: {str(e)}")

    def process_all_files(self) -> None:
        """Process all EOL report files in the root folder"""
        for root, dirs, files in os.walk(self.root_folder):
            for file in files:
                if file.endswith('-EOL_Report.csv') and file[0].isdigit():
                    if file.lower().startswith(('test', 'bble')):
                        continue
                    file_path = os.path.join(root, file)
                    self.process_file(file_path)
        
        print("Processing complete!")

def main():
    # Configure folders
    output_folder = r'Y:\NAV\01_Projects\0_KMS_3D_OBN_MT3007424\Vessel_Data_Analysis'
    root_folder = r'Z:\MT3007424\Murphy_KMS_3D_OBN\00_NAV'
    
    # Create and run analyzer
    analyzer = VesselDataAnalyzer(root_folder, output_folder)
    analyzer.process_all_files()

if __name__ == "__main__":
    main() 
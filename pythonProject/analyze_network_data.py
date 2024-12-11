import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Dict, Tuple

class NetworkDataAnalyzer:
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

    def process_network_quality(self, lines: List[str], line_name: str) -> pd.DataFrame:
        """Process network quality data and create visualization"""
        section_data, _ = self.extract_section_data(lines, "Network Quality", "Shot Point Interval")
        if not section_data:
            return None

        # Process data
        data = []
        for line in section_data[2:]:  # Skip header rows
            try:
                parts = line.strip().split(',')
                if len(parts) >= 4:
                    data.append({
                        'Shot': int(parts[0]),
                        'Time': parts[1],
                        'DOF': float(parts[2]),
                        'Quality': float(parts[3])
                    })
            except (ValueError, IndexError):
                continue

        if not data:
            return None

        df = pd.DataFrame(data)
        
        # Create plot
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12), sharex=True)
        
        # Plot DOF
        ax1.plot(df['Shot'], df['DOF'], label='DOF', color='blue')
        ax1.set_ylabel('DOF')
        ax1.grid(True)
        ax1.legend()
        
        # Plot Quality
        ax2.plot(df['Shot'], df['Quality'], label='Quality', color='green')
        ax2.set_ylabel('Quality')
        ax2.grid(True)
        ax2.legend()
        
        # Set common title and x-label
        fig.suptitle(f'Line {line_name}: Network Quality Parameters')
        ax2.set_xlabel('Shot Number')
        
        # Add statistics text boxes
        dof_stats = (f'DOF Statistics:\n'
                    f'Average: {df["DOF"].mean():.2f}\n'
                    f'Maximum: {df["DOF"].max():.2f}\n'
                    f'Minimum: {df["DOF"].min():.2f}\n'
                    f'Std Dev: {df["DOF"].std():.2f}')
        
        quality_stats = (f'Quality Statistics:\n'
                        f'Average: {df["Quality"].mean():.3f}\n'
                        f'Maximum: {df["Quality"].max():.3f}\n'
                        f'Minimum: {df["Quality"].min():.3f}\n'
                        f'Std Dev: {df["Quality"].std():.3f}')
        
        ax1.text(0.02, 0.98, dof_stats,
                transform=ax1.transAxes,
                verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        ax2.text(0.02, 0.98, quality_stats,
                transform=ax2.transAxes,
                verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Save plot
        plt.tight_layout()
        plt.savefig(
            os.path.join(self.output_folder, f'{line_name}_network_quality.png'),
            dpi=300,
            bbox_inches='tight'
        )
        plt.close()
        
        return df

    def process_shot_interval(self, lines: List[str], line_name: str) -> pd.DataFrame:
        """Process shot point interval data and create visualization"""
        section_data, _ = self.extract_section_data(lines, "Shot Point Interval", "Vessel CMG")
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
                        'Interval': float(parts[2])
                    })
            except (ValueError, IndexError):
                continue

        if not data:
            return None

        df = pd.DataFrame(data)
        
        # Create plot
        plt.figure(figsize=(15, 8))
        
        # Plot shot interval
        plt.plot(df['Shot'], df['Interval'], label='Shot Interval')
        
        # Calculate and plot statistics
        avg_interval = df['Interval'].mean()
        std_interval = df['Interval'].std()
        
        plt.axhline(y=avg_interval, color='r', linestyle='--', 
                   label=f'Average: {avg_interval:.2f}m')
        plt.axhline(y=avg_interval + 2*std_interval, color='y', linestyle=':',
                   label=f'+2σ: {avg_interval + 2*std_interval:.2f}m')
        plt.axhline(y=avg_interval - 2*std_interval, color='y', linestyle=':',
                   label=f'-2σ: {avg_interval - 2*std_interval:.2f}m')
        
        plt.title(f'Line {line_name}: Shot Point Interval')
        plt.xlabel('Shot Number')
        plt.ylabel('Interval (meters)')
        plt.grid(True)
        plt.legend()
        
        # Add statistics text box
        stats_text = (f'Statistics:\n'
                     f'Shots: {len(df)}\n'
                     f'Average: {avg_interval:.2f}m\n'
                     f'Std Dev: {std_interval:.2f}m\n'
                     f'Maximum: {df["Interval"].max():.2f}m\n'
                     f'Minimum: {df["Interval"].min():.2f}m')
        
        plt.text(0.02, 0.98, stats_text,
                transform=plt.gca().transAxes,
                verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Save plot
        plt.savefig(
            os.path.join(self.output_folder, f'{line_name}_shot_interval.png'),
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
            
            # Process network quality and shot interval data
            network_df = self.process_network_quality(lines, line_name)
            interval_df = self.process_shot_interval(lines, line_name)
            
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
    output_folder = r'Y:\NAV\01_Projects\0_KMS_3D_OBN_MT3007424\Network_Analysis'
    root_folder = r'Z:\MT3007424\Murphy_KMS_3D_OBN\00_NAV'
    
    # Create and run analyzer
    analyzer = NetworkDataAnalyzer(root_folder, output_folder)
    analyzer.process_all_files()

if __name__ == "__main__":
    main() 
# Twitter Followers Plotter

This directory contains a local script to fetch historical data from S3 and generate a plot of Twitter followers over time for the current year.

## Files

- `plot_twitter_followers.py` - Main Python script that fetches data from S3 and creates the plot
- `requirements.txt` - Python dependencies needed for the plotting script
- `run_twitter_plot.sh` - Shell script to set up environment and run the plotter
- `README.md` - This file

## Usage

### Quick Start

Simply run the setup script:

```bash
./run_twitter_plot.sh
```

This script will:
1. Create a virtual environment (`plot-venv`)
2. Install required dependencies (boto3, matplotlib, python-dotenv)
3. Load AWS credentials from `../lambda_function/.env`
4. Fetch historical data from S3
5. Generate and display a plot of Twitter followers for the current year
6. Save the plot as a PNG file

### Manual Usage

If you prefer to run manually:

```bash
# Create and activate virtual environment
python3 -m venv plot-venv
source plot-venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the script
python3 plot_twitter_followers.py
```

## Requirements

- Python 3.6+
- AWS credentials configured in `../lambda_function/.env`
- Internet connection to fetch data from S3

## Output

The script will:
- Display a matplotlib plot showing Twitter followers over time
- Save the plot as `twitter_followers_YYYY.png` (where YYYY is the current year)
- Show statistics including current, minimum, maximum, and total growth

## Notes

- This script is for local analysis only and should not be deployed
- It uses the same S3 bucket and credentials as the main Lambda function
- The plot will only show data for the current year
- If the main historical data file is not found, it will try the backup file

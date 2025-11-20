import pandas as pd
import psycopg2

# Read CSV into a Pandas DataFrame
df = pd.read_csv("../data/vietrace/scoreboard.csv", header=0)

# Connect to PostgreSQL DB with registered credentials
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="mydb",
    user="nguyenthanh",
    password="16042005"
)
cur = conn.cursor()

# Create table

cur.execute(query="""
CREATE TABLE vietrace (
RANK INT PRIMARY KEY,
NAME TEXT,
DEPARTMENT TEXT,
STAFFCODE TEXT,
RUN_DISTANCE DOUBLE PRECISION,
WALK_DISTANCE DOUBLE PRECISION,
TOTAL_DISTANCE DOUBLE PRECISION,
PACE_MINUTES TEXT,
PACE_SECONDS TEXT,
SPEED DOUBLE PRECISION);
""")


# Iterate through each row
for _, row in df.iterrows():
    cur.execute(
        """
        INSERT INTO vietrace (
            RANK,
            NAME,
            DEPARTMENT,
            STAFFCODE,
            RUN_DISTANCE,
            WALK_DISTANCE,
            TOTAL_DISTANCE,
            PACE_MINUTES,
            PACE_SECONDS,
            SPEED
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            row['Rank'],
            row['Name'],
            row['Department'],
            row['Staff Code'],
            row['Run Distance (km)'],
            row['Walk Distance (km)'],
            row['Total Distance (km)'],
            row['Pace Minutes'],
            row['Pace Seconds'],
            row['Speed (km/h)'],
        )
    )

conn.commit()
cur.close()
conn.close()

# Finished loading data
print("CSV data loaded into PostgreSQL!")
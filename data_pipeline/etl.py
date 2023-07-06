def data_cleaning(df):
    # Drop duplicate rows
    df = df.drop_duplicates()

    # Remove rows with missing values
    df = df.dropna()
    
    return df
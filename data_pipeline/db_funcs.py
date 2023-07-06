TABLE_NAME = "VGSales"

def prep_insert_qry(colnames):
    """this query is secure as long as `colnames` contains trusted data
    standard parametrized query mechanism secures `args`"""

    binds,use = [],[]

    for colname in colnames:
        use.extend([colname,","])
        binds.extend(["%s",","])

    parts = [f"insert ignore into {TABLE_NAME} ("]
    use = use[:-1]
    binds = binds[:-1]
    
    parts.extend(use)
    parts.append(") values(")
    parts.extend(binds)
    parts.append(")")

    qry = " ".join(parts)

    return qry
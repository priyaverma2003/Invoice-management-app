import mysql.connector
from datetime import date

# This assumes your connection code is in a separate file called 'db_connection.py'
# If you prefer to put all the code in one file, just move your connection logic
# to the top of this file and call the connection object directly.

# Reusing your provided connection function for clarity
def get_db_connection():
    """Establishes and returns a connection to the MySQL database."""
    try:
        connection = mysql.connector.connect(
            host='127.0.0.1',
            database='invoicing_db',
            user='root',
            password='____Priya13_'
        )
        return connection
    except mysql.connector.Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def compute_aging_bucket(due_date, today):
    """
    Calculates the aging bucket for a given due date.
    
    Args:
        due_date (date): The due date of the invoice.
        today (date): The current date.
        
    Returns:
        str: The aging bucket category.
    """
    days_overdue = (today - due_date).days
    
    if days_overdue > 90:
        return '90+ days overdue'
    elif days_overdue > 60:
        return '61-90 days overdue'
    elif days_overdue > 30:
        return '31-60 days overdue'
    elif days_overdue > 0:
        return '0-30 days overdue'
    else:
        return 'On Time'


def list_invoices():
    """
    Retrieves a list of invoices with calculated fields like outstanding balance and aging bucket.
    
    Returns:
        list: A list of dictionaries, where each dictionary represents an invoice.
    """
    connection = get_db_connection()
    if connection is None:
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        # SQL query to get all invoice details and sums of payments
        query = """
        SELECT
            c.name AS customer_name,
            i.amount,
            COALESCE(SUM(p.amount), 0) AS total_paid,
            i.amount - COALESCE(SUM(p.amount), 0) AS outstanding,
            i.due_date,
            i.invoice_date,
            i.invoice_id
        FROM invoices AS i
        LEFT JOIN payments AS p ON i.invoice_id = p.invoice_id
        JOIN customers AS c ON i.customer_id = c.customer_id
        GROUP BY i.invoice_id
        ORDER BY i.due_date DESC;
        """
        cursor.execute(query)
        invoices = cursor.fetchall()

        # Add the aging bucket to each invoice using the helper function
        for invoice in invoices:
            invoice['aging_bucket'] = compute_aging_bucket(invoice['due_date'], date.today())
        
        return invoices

    except mysql.connector.Error as e:
        print(f"Error listing invoices: {e}")
        return []
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def add_payment(invoice_id, amount, payment_date=date.today()):
    """
    Adds a new payment record for a given invoice.
    
    Args:
        invoice_id (int): The ID of the invoice being paid.
        amount (float): The amount of the payment.
        payment_date (date, optional): The date of the payment. Defaults to today.
        
    Returns:
        bool: True if the payment was added successfully, False otherwise.
    """
    connection = get_db_connection()
    if connection is None:
        return False
    
    try:
        cursor = connection.cursor()
        query = "INSERT INTO payments (invoice_id, amount, payment_date) VALUES (%s, %s, %s)"
        cursor.execute(query, (invoice_id, amount, payment_date))
        connection.commit()
        return True
    except mysql.connector.Error as e:
        connection.rollback()
        print(f"Error adding payment: {e}")
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def get_top_5_customers():
    """
    Retrieves the top 5 customers by total outstanding amount.
    
    Returns:
        list: A list of dictionaries, each containing a customer's name and total outstanding amount.
    """
    connection = get_db_connection()
    if connection is None:
        return []

    try:
        cursor = connection.cursor(dictionary=True)
        query = """
        SELECT
            c.name AS customer_name,
            SUM(i.amount - COALESCE(p.total_paid, 0)) AS total_outstanding
        FROM customers AS c
        JOIN invoices AS i ON c.customer_id = i.customer_id
        LEFT JOIN (
            SELECT
                invoice_id,
                SUM(amount) AS total_paid
            FROM payments
            GROUP BY invoice_id
        ) AS p ON i.invoice_id = p.invoice_id
        GROUP BY c.name
        ORDER BY total_outstanding DESC
        LIMIT 5;
        """
        cursor.execute(query)
        return cursor.fetchall()
    except mysql.connector.Error as e:
        print(f"Error getting top 5 customers: {e}")
        return []
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Example usage of the functions
if __name__ == '__main__':
    print("Listing all invoices:")
    invoices = list_invoices()
    print(invoices)

    print("\nAdding a new payment for invoice_id 1 with an amount of 50.00:")
    success = add_payment(1, 50.00)
    print("Payment added successfully." if success else "Failed to add payment.")

    print("\nGetting top 5 customers by outstanding amount:")
    top_customers = get_top_5_customers()
    print(top_customers)

# In your Python logic file 

def get_kpi_data():
    """
    Calculates and returns key performance indicators (KPIs).
    """
    connection = get_db_connection()
    if connection is None:
        return {}

    try:
        cursor = connection.cursor(dictionary=True)
        
        # Query for Total Invoiced and Total Received
        kpi_query = """
        SELECT
            COALESCE(SUM(i.amount), 0) AS total_invoiced,
            COALESCE(SUM(p.amount), 0) AS total_received,
            SUM(CASE WHEN i.due_date < CURDATE() THEN 1 ELSE 0 END) AS overdue_count,
            COUNT(i.invoice_id) AS total_invoices
        FROM invoices AS i
        LEFT JOIN payments AS p ON i.invoice_id = p.invoice_id;
        """
        cursor.execute(kpi_query)
        kpi_results = cursor.fetchone()

        # Query for Total Outstanding
        outstanding_query = """
        SELECT
            COALESCE(SUM(i.amount - COALESCE(p.total_paid, 0)), 0) AS total_outstanding
        FROM invoices AS i
        LEFT JOIN (
            SELECT
                invoice_id,
                SUM(amount) AS total_paid
            FROM payments
            GROUP BY invoice_id
        ) AS p ON i.invoice_id = p.invoice_id;
        """
        cursor.execute(outstanding_query)
        outstanding_result = cursor.fetchone()
        
        total_invoiced = kpi_results['total_invoiced'] or 0
        total_received = kpi_results['total_received'] or 0
        total_outstanding = outstanding_result['total_outstanding'] or 0
        
        overdue_invoices = kpi_results['overdue_count']
        total_invoices = kpi_results['total_invoices']
        percent_overdue = (overdue_invoices / total_invoices) * 100 if total_invoices > 0 else 0

        return {
            'total_invoiced': float(total_invoiced),
            'total_received': float(total_received),
            'total_outstanding': float(total_outstanding),
            'percent_overdue': float(percent_overdue)
        }

    except Exception as e:
        print(f"Error fetching KPIs: {e}")
        return {}
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


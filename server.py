from flask import Flask, render_template, request, jsonify
from db_connect import list_invoices, add_payment, get_top_5_customers

app = Flask(__name__)

# Route to serve the main HTML page
@app.route('/')
def index():
    return render_template('index.html')

# API endpoint to get all invoice data
@app.route('/api/invoices')
def get_invoices():
    invoices = list_invoices()
    return jsonify(invoices)

# API endpoint to record a payment
@app.route('/api/record-payment', methods=['POST'])
def record_payment():
    data = request.json
    invoice_id = data.get('invoice_id')
    amount = data.get('amount')
    payment_date = data.get('payment_date')
    
    success = add_payment(invoice_id, amount, payment_date)
    return jsonify({'success': success})

# API endpoint for KPI tiles
@app.route('/api/kpis')
def get_kpis():
    #  write functions to get these values from the database
    total_invoiced = 0 # Placeholder
    total_received = 0 # Placeholder
    total_outstanding = 0 # Placeholder
    percent_overdue = 0 # Placeholder
    return jsonify({
        'total_invoiced': total_invoiced,
        'total_received': total_received,
        'total_outstanding': total_outstanding,
        'percent_overdue': percent_overdue
    })

# API endpoint for the chart data
@app.route('/api/chart-data')
def get_chart_data():
    top_customers = get_top_5_customers()
    return jsonify(top_customers)

if __name__ == '__main__':
    app.run(debug=True)
import os
import json
import xmltodict
import pandas as pd
import streamlit as st
import plotly.express as px
from pymongo import MongoClient
import plotly.figure_factory as ff
from pymongo.server_api import ServerApi

# MongoDB connection settings
mongo_uri = "mongodb+srv://thasnihakeem2017:m4PIT69br5a1vGI1@sale.cup3qfg.mongodb.net/?retryWrites=true&w=majority"
database_name = "sales"
collection_name = "bill"

# Connect to MongoDB
client = MongoClient(mongo_uri, server_api=ServerApi('1'))
db = client[database_name]
collection = db[collection_name]

def convert_xml_to_json(xml_content):
    # Convert XML to JSON
    json_data = xmltodict.parse(xml_content, xml_attribs=True)
    return json_data

def save_to_mongodb(json_data):
    # Insert the JSON data into MongoDB
    collection.insert_one(json_data)

def show_store_details(bill_barcode):
    if bill_barcode is None:
        latest_document = collection.find_one(sort=[('_id', -1)])
    else:
        latest_document = collection.find_one({"POSLog.Transaction.WN:Barcode": bill_barcode})

    if latest_document:
        store_details = {
            'RetailStoreID': latest_document['POSLog']['Transaction']['RetailStoreID'],
            'OrganizationID': latest_document['POSLog']['Transaction']['OrganizationHierarchy']['@ID'],
            'OrganizationText': latest_document['POSLog']['Transaction']['OrganizationHierarchy']['#text'],
            'WorkstationID': latest_document['POSLog']['Transaction']['WorkstationID'],
            'SequenceNumber': latest_document['POSLog']['Transaction']['SequenceNumber'],
            'BusinessDayDate': latest_document['POSLog']['Transaction']['BusinessDayDate'],
            'BeginDateTime': latest_document['POSLog']['Transaction']['BeginDateTime'],
            'EndDateTime': latest_document['POSLog']['Transaction']['EndDateTime'],
            'TransactionType': latest_document['POSLog']['Transaction']['TransactionType']}
        df = pd.DataFrame([store_details])

        # Display the DataFrame in a table
        st.subheader("Store Details")
        st.table(df)
    else:
        st.write("No uploaded XML file found.")
    
def show_operator_details(bill_barcode):
    if bill_barcode is None:
        latest_document = collection.find_one(sort=[('_id', -1)])
    else:
        latest_document = collection.find_one({"POSLog.Transaction.WN:Barcode": bill_barcode})

    if latest_document:
        # Extract operator details from the latest document
        operator_details = {
            'OperatorID': latest_document['POSLog']['Transaction']['OperatorID']['#text'],
            'OperatorName': latest_document['POSLog']['Transaction']['OperatorID']['@OperatorName'],
            'RetailStoreID': latest_document['POSLog']['Transaction']['RetailStoreID'],
            'OrganizationID': latest_document['POSLog']['Transaction']['OrganizationHierarchy']['@ID'],
            'OrganizationText': latest_document['POSLog']['Transaction']['OrganizationHierarchy']['#text'],
            'WorkstationID': latest_document['POSLog']['Transaction']['WorkstationID'],
            'BusinessDayDate': latest_document['POSLog']['Transaction']['BusinessDayDate'],
            'BeginDateTime': latest_document['POSLog']['Transaction']['BeginDateTime'],
            'EndDateTime': latest_document['POSLog']['Transaction']['EndDateTime'],
        }

        # Create a DataFrame from the extracted operator details
        df = pd.DataFrame([operator_details])

        # Display the DataFrame in a table
        st.subheader("Operator Details")
        st.table(df)
    else:
        st.write("No uploaded XML file found.")


def show_customer_details(bill_barcode):
    if bill_barcode is None:
        latest_document = collection.find_one(sort=[('_id', -1)])
    else:
        latest_document = collection.find_one({"POSLog.Transaction.WN:Barcode": bill_barcode})
    if latest_document:
        # Extract customer details from the latest document
        customer_details = {
            'CustomerID': latest_document['POSLog']['Transaction']['RetailTransaction']['Customer']['CustomerID'],
            'CustomerName': latest_document['POSLog']['Transaction']['RetailTransaction']['Customer']['CustomerName'].get('Name', [{}])[0].get('#text', None),
            'Mobile': latest_document['POSLog']['Transaction']['Mobile'],
            'LoyaltyCardID': latest_document['POSLog']['Transaction']['RetailTransaction']['Customer'].get('WN:LoyaltyCardID', None)}

        # Create a DataFrame from the extracted customer details
        df = pd.DataFrame([customer_details])

        # Display the DataFrame in a table
        st.subheader("Customer Details")
        st.table(df)
    else:
        st.write("No uploaded XML file found.")


def show_product_details(bill_barcode):
    if bill_barcode is None:
        latest_document = collection.find_one(sort=[('_id', -1)])
    else:
        latest_document = collection.find_one({"POSLog.Transaction.WN:Barcode": bill_barcode})

    if latest_document:
        # Define a list to store selected fields from each LineItem
        selected_fields_list = []

        # Process each LineItem in the latest document and extract selected fields
        for item in latest_document['POSLog']['Transaction']['RetailTransaction']['LineItem']:
            sale = item.get('Sale', {})
            tax_list = sale.get('Tax', [{}])

            selected_fields = {
                'ItemType': sale.get('@ItemType'),
                'HSNCode': sale.get('WN:HSNCode'),
                'ItemID': sale.get('ItemID'),
                'POSItemID': sale.get('POSIdentity', [{}])[0].get('POSItemID'),
                'MerchandiseHierarchy': sale.get('MerchandiseHierarchy', [{}])[-2].get('#text') if len(sale.get('MerchandiseHierarchy', [{}])) > 1 else None,
                'Description': sale.get('Description'),
                'Brand': sale.get('WN:Brand'),
                'UnitListPrice': sale.get('UnitListPrice'),
                'RegularSalesUnitPrice': sale.get('RegularSalesUnitPrice'),
                'MaxRetailPrice': sale.get('MaxRetailPrice'),
                'ActualSalesUnitPrice': sale.get('ActualSalesUnitPrice'),
                'ExtendedAmount': sale.get('ExtendedAmount'),
                'DiscountAmount': sale.get('DiscountAmount'),
                'QuantityUnits': sale.get('Quantity', {}).get('@Units'),
                'QuantityUnitOfMeasureCode': sale.get('Quantity', {}).get('@UnitOfMeasureCode'),
                'TaxAuthority1': tax_list[1].get('TaxAuthority') if len(tax_list) > 1 else None,
                'TaxAmount1': tax_list[0].get('AmountRounded') if len(tax_list) > 0 else None,
                'TaxPercent1': tax_list[0].get('Percent') if len(tax_list) > 0 else 0,
                'TaxRuleID1': tax_list[0].get('TaxRuleID') if len(tax_list) > 0 else None,
                'TaxGroupID1': tax_list[0].get('TaxGroupID') if len(tax_list) > 0 else None,
                'ReceiptPrintCode': tax_list[0].get('ReceiptPrintCode') if len(tax_list) > 0 else None,
                'TaxAuthority2': tax_list[1].get('TaxAuthority') if len(tax_list) > 1 else None,
                'TaxAmount2': tax_list[0].get('AmountRounded') if len(tax_list) > 0 else None,
                'TaxPercent2': tax_list[0].get('Percent') if len(tax_list) > 0 else 0,
                'TaxRuleID2': tax_list[0].get('TaxRuleID') if len(tax_list) > 0 else None,
                'TaxGroupID2': tax_list[0].get('TaxGroupID') if len(tax_list) > 0 else None,
                'ReceiptPrintCode2': tax_list[0].get('ReceiptPrintCode') if len(tax_list) < 0 else 'SGST'
            }
            
            if selected_fields['ItemID'] is not None:
                selected_fields_list.append(selected_fields)

        # Create a DataFrame from the list of selected fields
        df = pd.DataFrame(selected_fields_list)

        # Display the DataFrame in a table
        st.subheader("Product Details")
        st.table(df)

        # Calculate TaxAmount
        df['TaxAmount'] = df['TaxAmount1'] + df['TaxAmount2']

        # Create a bar chart using Plotly Express with Quantity, Discount, and beautiful color
        fig = px.bar(df, x='Description', y='ExtendedAmount', color='Brand',
                     title='Product Details for Each Product',
                     labels={'ExtendedAmount': 'Total Amount'},
                     hover_data=['QuantityUnits', 'MerchandiseHierarchy', 'TaxGroupID1', 'TaxAmount'],
                     color_discrete_sequence=px.colors.qualitative.Set3)
        st.plotly_chart(fig)
    else:
        st.write("No uploaded XML file found.")


def show_price_details(bill_barcode):
    if bill_barcode is None:
        latest_document = collection.find_one(sort=[('_id', -1)])
    else:
        latest_document = collection.find_one({"POSLog.Transaction.WN:Barcode": bill_barcode})

    if latest_document:
        line_items = latest_document['POSLog']['Transaction']['RetailTransaction']['LineItem']

        # Check if there are at least 8 LineItems
        if len(line_items) > 4:
            selected_fields = {
                'CustomerID': latest_document['POSLog']['Transaction']['RetailTransaction']['Customer']['CustomerID'],
                'Total Quantity': latest_document['POSLog']['Transaction']['RetailTransaction']['Total'][5]['#text'],
                'NetAmount': latest_document['POSLog']['Transaction']['RetailTransaction']['Total'][0]['#text'],
                'TaxAmount': latest_document['POSLog']['Transaction']['RetailTransaction']['Total'][1]['#text'],
                'Total Amount': latest_document['POSLog']['Transaction']['RetailTransaction']['Total'][2]['#text'],
                'Discount Amount': latest_document['POSLog']['Transaction']['RetailTransaction']['Total'][4]['#text']}
            
            # Create a DataFrame from the selected fields
            df = pd.DataFrame([selected_fields])
            st.subheader("Price Details")
            st.table(df)
        else:
            st.write("Not enough LineItems in the document.")
    else:
        st.write("No uploaded XML file found.")


def show_TAX_details(bill_barcode):
    if bill_barcode is None:
        latest_document = collection.find_one(sort=[('_id', -1)])
    else:
        latest_document = collection.find_one({"POSLog.Transaction.WN:Barcode": bill_barcode})

    if latest_document:
        selected_tax_fields_list = []
        for item in latest_document['POSLog']['Transaction']['RetailTransaction']['LineItem']:
            tax = item.get('Tax', {})  # Extract Tax information
            selected_fields = {
                'TaxAuthority': tax.get('TaxAuthority'),
                'TaxableAmount': tax.get('TaxableAmount', {}).get('#text'),
                'AmountRounded': tax.get('AmountRounded'),
                'TaxRuleID': tax.get('TaxRuleID'),
                'Percent': tax.get('Percent'),
                'TaxGroupID': tax.get('TaxGroupID'),
                'ReceiptPrintCode': tax.get('ReceiptPrintCode')}
            if selected_fields['TaxAuthority'] is not None:
                    selected_tax_fields_list.append(selected_fields)

        # Create a DataFrame from the list of selected tax fields
        df = pd.DataFrame(selected_tax_fields_list)
        st.subheader("Tax Details")
        st.table(df)
    else:
        st.write("No uploaded XML file found.")


def show_payment_details(bill_barcode):
    if bill_barcode is None:
        latest_document = collection.find_one(sort=[('_id', -1)])
    else:
        latest_document = collection.find_one({"POSLog.Transaction.WN:Barcode": bill_barcode})

    if latest_document:
        # Define a list to store selected fields from each LineItem
        selected_fields_list = []

        # Process each LineItem in the latest document and extract selected fields
        for item in latest_document['POSLog']['Transaction']['RetailTransaction']['LineItem']:
            tender = item.get('Tender', {})
            if tender.get('@TenderType') != 'NONE':
                authorization = tender.get('Authorization', {})
                credit_debit = tender.get('CreditDebit', {})
                
                selected_fields = {
                    'TenderType': tender.get('@TenderType'),
                    'ExternalTenderType': tender.get('@WN:ExternalTenderType'),
                    'CPGName': tender.get('CPGName'),
                    'AuthorizationDescription': authorization.get('AuthorizationDescription'),
                    'CardType': credit_debit.get('@CardType'),
                    'PrimaryAccountNumber': tender.get('AccountNmbr', credit_debit.get('PrimaryAccountNumber')),
                    'TenderAmount': tender.get('Amount')
                }
                if selected_fields['TenderType'] is not None:
                    selected_fields_list.append(selected_fields)

        # Create a DataFrame from the list of selected fields
        df = pd.DataFrame(selected_fields_list)

        # Display the DataFrame in a table
        st.subheader("Payment Details")
        st.table(df)
    else:
        st.write("No uploaded XML file found.")


def main():
    st.title("Information Desk")

    # Option 1: Upload XML file
    uploaded_file = st.file_uploader("Upload XML File", type=["xml"])
    
    # Initialize bill_barcode
    bill_barcode = None

    if uploaded_file is not None:
        # Process the uploaded XML file
        xml_content = uploaded_file.read()
        json_data = convert_xml_to_json(xml_content)

        # Save to MongoDB
        save_to_mongodb(json_data)

        st.write("XML file content has been uploaded and saved to MongoDB.")

        # Provide options to view details
        selected_option = st.selectbox("Select Details to View", ["", "Store Details", "Operator Details", "Customer Details", "Product Details", "Price Details", "Tax Details", "Payment Details"])

        if selected_option == "Store Details":
            show_store_details(bill_barcode)
        elif selected_option == "Operator Details":
            show_operator_details(bill_barcode)
        elif selected_option == "Customer Details":
            show_customer_details(bill_barcode)
        elif selected_option == "Product Details":
            show_product_details(bill_barcode)
        elif selected_option == "Price Details":
            show_price_details(bill_barcode)
        elif selected_option == "Tax Details":
            show_TAX_details(bill_barcode)
        elif selected_option == "Payment Details":
            show_payment_details(bill_barcode)

    # Option 2: Enter bill barcode number
    bill_barcode = st.text_input("Enter Bill Barcode Number:")
    if bill_barcode:
        st.write(f"Bill Barcode Number Entered: {bill_barcode}")
        selected_option = st.selectbox("Select Details to View", ["", "Store Details", "Operator Details", "Customer Details", "Product Details", "Price Details", "Tax Details", "Payment Details"])
        if selected_option == "Store Details":
            show_store_details(bill_barcode)
        elif selected_option == "Operator Details":
            show_operator_details(bill_barcode)
        elif selected_option == "Customer Details":
            show_customer_details(bill_barcode)
        elif selected_option == "Product Details":
            show_product_details(bill_barcode)
        elif selected_option == "Price Details":
            show_price_details(bill_barcode)
        elif selected_option == "Tax Details":
            show_TAX_details(bill_barcode)
        elif selected_option == "Payment Details":
            show_payment_details(bill_barcode)
    else:
        st.write(f"No details found for the given barcode: {bill_barcode}")

if __name__ == "__main__":
    main()

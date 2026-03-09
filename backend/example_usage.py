from mpesa_client import MpesaB2BClient
import json

# Initialize the client
mpesa = MpesaB2BClient()

# Example 1: Generate session only
try:
    session = mpesa.generate_session()
    print(f"✅ Session generated: {session}")
except Exception as e:
    print(f"❌ Session failed: {e}")

# Example 2: Process B2B payment
try:
    # University pays 50 LSL to verify certificate CERT-2024-001
    response = mpesa.b2b_payment(
        university_code="UNI001",        # University's code
        amount="5000",                    # 50.00 LSL
        certificate_reference="CERT-2024-001",
        description="Certificate verification fee"
    )
    
    print("\n📤 Payment Response:")
    print(json.dumps(response, indent=2))
    
    # Check if payment was successful
    if mpesa.is_payment_successful(response):
        print(f"\n✅ Payment successful!")
        print(f"Transaction ID: {response.get('output_TransactionID')}")
        print(f"Conversation ID: {response.get('output_ConversationID')}")
        
        # Save these for your records
        transaction_id = response.get('output_TransactionID')
        conversation_id = response.get('output_ConversationID')
        
        # TODO: Update your database - payment received, issue certificate
        
    else:
        print(f"\n❌ Payment failed: {mpesa.get_response_message(response)}")
        
except Exception as e:
    print(f"❌ Error: {e}")

# Example 3: Query transaction status
try:
    status = mpesa.query_transaction("VERIFY-CERT-2024-001")
    print("\n📊 Transaction Status:")
    print(json.dumps(status, indent=2))
except Exception as e:
    print(f"❌ Query failed: {e}")

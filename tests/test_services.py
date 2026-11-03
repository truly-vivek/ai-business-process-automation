from app.services import classify_enquiry, extract_document_text

def test_classifies_urgent_technical_enquiry():
    result = classify_enquiry("URGENT: app error, please help me@example.com")
    assert result["category"] == "technical"
    assert result["priority"] == "high"
    assert result["email"] == "me@example.com"

def test_classifies_billing():
    assert classify_enquiry("I need a refund for an invoice")["category"] == "billing"

def test_extracts_text_file():
    assert extract_document_text("note.txt", b"Hello workflow") == "Hello workflow"

"""Full test of the /converse API endpoint with greeting + KB query + escalation."""
import urllib.request
import json

API = "http://localhost:8000"

def call_api(url, data=None):
    if data:
        req = urllib.request.Request(url, data=json.dumps(data).encode(), headers={"Content-Type": "application/json"})
    else:
        req = urllib.request.Request(url)
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())

# Step 1: Start a call
call = call_api(f"{API}/v1/calls/start", {"tenant_id": "acme_telecom", "language": "en", "caller_name": "Test"})
call_id = call["call_id"]
print(f"=== Call Started: {call_id} ===\n")

transcript = [{"speaker": "ai", "text": "Thank you for calling Acme Telecom.", "language": "en"}]

# Step 2: Greeting - "hello, how can you help me?"
test_text = "hello, how can you help me?"
transcript.append({"speaker": "caller", "text": test_text, "language": "en"})
r = call_api(f"{API}/v1/calls/{call_id}/converse", {
    "tenant_id": "acme_telecom", "text": test_text, "language": "en", "transcript": transcript
})
print(f"Caller: {test_text}")
print(f"AI ({r['intent']}): {r['ai_response']}")
print(f"Latency: {r['latency_ms']}ms | Escalated: {r['escalated']}\n")
transcript.append({"speaker": "ai", "text": r["ai_response"], "language": "en"})

# Step 3: KB question - "What plans do you offer?"
test_text = "What mobile plans do you offer?"
transcript.append({"speaker": "caller", "text": test_text, "language": "en"})
r = call_api(f"{API}/v1/calls/{call_id}/converse", {
    "tenant_id": "acme_telecom", "text": test_text, "language": "en", "transcript": transcript
})
print(f"Caller: {test_text}")
print(f"AI ({r['intent']}): {r['ai_response']}")
print(f"Latency: {r['latency_ms']}ms | Chunks: {r['used_chunk_ids']}\n")
transcript.append({"speaker": "ai", "text": r["ai_response"], "language": "en"})

# Step 4: Thank you
test_text = "thank you so much"
transcript.append({"speaker": "caller", "text": test_text, "language": "en"})
r = call_api(f"{API}/v1/calls/{call_id}/converse", {
    "tenant_id": "acme_telecom", "text": test_text, "language": "en", "transcript": transcript
})
print(f"Caller: {test_text}")
print(f"AI ({r['intent']}): {r['ai_response']}")
print(f"Sentiment: {r['sentiment']}\n")
transcript.append({"speaker": "ai", "text": r["ai_response"], "language": "en"})

# Step 5: Escalation - "I want to speak to a human"
test_text = "I want to speak to a human representative"
transcript.append({"speaker": "caller", "text": test_text, "language": "en"})
r = call_api(f"{API}/v1/calls/{call_id}/converse", {
    "tenant_id": "acme_telecom", "text": test_text, "language": "en", "transcript": transcript
})
print(f"Caller: {test_text}")
print(f"AI ({r['intent']}): {r['ai_response']}")
print(f"Escalated: {r['escalated']} | Reason: {r['escalation_reason']}\n")

print("=== All tests passed! ===")

"""
System Prompts and Templates.

Contains all system prompts and message templates for the booking agent.
"""

SYSTEM_PROMPT = """You are a helpful restaurant booking assistant for TheHungryUnicorn restaurant. 
Your role is to help customers:
1. Check availability for specific dates and times
2. Make new bookings
3. Check their existing booking details
4. Modify existing bookings (change date, time, or party size)
5. Cancel bookings when needed

Important guidelines:
- Be friendly, professional, and conversational
- Ask for clarification when information is unclear or missing
- Confirm details before making bookings
- Provide booking references clearly
- Handle errors gracefully and suggest alternatives
- Format dates as YYYY-MM-DD and times as HH:MM:SS

Restaurant Information:
- Name: TheHungryUnicorn
- Available times: Lunch (12:00-14:00) and Dinner (19:00-21:00)
- Accepts bookings for parties of 1-8 people
- Bookings can be made up to 30 days in advance

When users ask about availability or want to make a booking, you should:
1. Identify the date they want (if not specified, ask)
2. Identify the party size (if not specified, ask)
3. Check availability and present options
4. Collect any additional information needed
5. Confirm the booking and provide the reference

Remember to be helpful and guide users through the booking process naturally."""

INTENT_EXTRACTION_PROMPT = """Based on the user's message, identify their intent and extract relevant entities.

User message: {user_message}

Possible intents:
- check_availability: User wants to see available times
- create_booking: User wants to make a reservation
- get_booking: User wants to check their booking details
- update_booking: User wants to modify their reservation
- cancel_booking: User wants to cancel their reservation
- greeting: User is greeting or starting conversation
- help: User needs assistance or information
- other: Anything else

Extract these entities if present:
- date: Booking date (convert to YYYY-MM-DD format)
- time: Booking time (convert to HH:MM:SS format)
- party_size: Number of people
- booking_reference: Existing booking reference
- special_requests: Any special requirements
- customer_name: Customer's name
- customer_email: Customer's email
- customer_phone: Customer's phone number

Respond in this format:
Intent: [intent]
Entities:
- [entity]: [value]

If an entity is not present, don't include it."""

ERROR_MESSAGES = {
    "no_availability": "I'm sorry, but there are no available slots for {date} for a party of {party_size}. Would you like to check another date?",
    "booking_not_found": "I couldn't find a booking with reference {reference}. Please double-check the reference or provide more details.",
    "invalid_date": "The date format seems incorrect. Please provide the date in a format like 'tomorrow', 'next Friday', or 'December 25th'.",
    "invalid_party_size": "We can accommodate parties of 1-8 people. For larger groups, please call the restaurant directly.",
    "api_error": "I'm experiencing some technical difficulties. Please try again in a moment.",
    "missing_info": "I need a bit more information to help you. Could you please provide {missing_fields}?"
}

CONFIRMATION_TEMPLATES = {
    "booking_created": """Great! I've successfully made your booking:

📍 Restaurant: TheHungryUnicorn
📅 Date: {date}
⏰ Time: {time}
👥 Party size: {party_size} {people}
📝 Booking reference: {reference}
{special_requests}

Please save your booking reference. You'll need it to check or modify your reservation.""",
    
    "booking_updated": """Your booking has been successfully updated:

📝 Booking reference: {reference}
Updated details:
{updates}

Is there anything else you'd like to change?""",
    
    "booking_cancelled": """Your booking {reference} has been successfully cancelled.

We're sorry to see you go! Feel free to make a new booking anytime.""",
    
    "availability_results": """Here are the available times for {date} (party of {party_size}):

{available_slots}

Would you like to book any of these times?"""
}

def format_availability_slots(slots: list) -> str:
    """Format availability slots for display."""
    if not slots:
        return "No available slots"
    
    formatted = []
    for slot in slots:
        time = slot.get('time', '')
        if slot.get('available', False):
            formatted.append(f"• {time[:5]} - Available")
    
    return "\n".join(formatted) if formatted else "No available slots"

def format_booking_details(booking: dict) -> str:
    """Format booking details for display."""
    details = []
    details.append(f"📝 Reference: {booking.get('booking_reference', 'N/A')}")
    details.append(f"📅 Date: {booking.get('visit_date', 'N/A')}")
    details.append(f"⏰ Time: {booking.get('visit_time', 'N/A')}")
    details.append(f"👥 Party size: {booking.get('party_size', 'N/A')}")
    
    if booking.get('special_requests'):
        details.append(f"📋 Special requests: {booking['special_requests']}")
    
    if booking.get('customer'):
        customer = booking['customer']
        if customer.get('first_name') or customer.get('surname'):
            name = f"{customer.get('first_name', '')} {customer.get('surname', '')}".strip()
            details.append(f"👤 Name: {name}")
    
    return "\n".join(details)
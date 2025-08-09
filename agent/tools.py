"""
Agent Tools for Restaurant Booking Operations.

Provides tool functions that the agent can use to interact with the booking API.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import re
import logging
from dateutil import parser
from dateutil.relativedelta import relativedelta

from agent.api_client import BookingAPIClient
from agent.prompts import format_availability_slots, format_booking_details

logger = logging.getLogger(__name__)


class BookingTools:
    """Collection of tools for restaurant booking operations."""
    
    def __init__(self, api_client: BookingAPIClient):
        """
        Initialize booking tools.
        
        Args:
            api_client: API client instance
        """
        self.api_client = api_client
    
    async def check_availability(
        self,
        date_str: str,
        party_size: int
    ) -> Dict[str, Any]:
        """
        Check availability for a given date and party size.
        
        Args:
            date_str: Date string (will be parsed and formatted)
            party_size: Number of people
            
        Returns:
            Formatted availability information
        """
        try:
            # Parse and format date
            formatted_date = self._parse_date(date_str)
            
            # Call API
            result = await self.api_client.check_availability(
                visit_date=formatted_date,
                party_size=party_size
            )
            
            # Format response
            slots = result.get('available_slots', [])
            formatted_slots = format_availability_slots(slots)
            
            return {
                "success": True,
                "date": formatted_date,
                "party_size": party_size,
                "formatted_slots": formatted_slots,
                "raw_slots": slots,
                "message": f"Found {len([s for s in slots if s.get('available')])} available slots"
            }
        except Exception as e:
            logger.error(f"Error checking availability: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to check availability"
            }
    
    async def create_booking(
        self,
        date_str: str,
        time_str: str,
        party_size: int,
        customer_info: Optional[Dict[str, Any]] = None,
        special_requests: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new booking.
        
        Args:
            date_str: Date string
            time_str: Time string
            party_size: Number of people
            customer_info: Customer details
            special_requests: Special requirements
            
        Returns:
            Booking confirmation details
        """
        try:
            # Parse and format date/time
            formatted_date = self._parse_date(date_str)
            formatted_time = self._parse_time(time_str)
            
            # Call API
            result = await self.api_client.create_booking(
                visit_date=formatted_date,
                visit_time=formatted_time,
                party_size=party_size,
                customer_info=customer_info,
                special_requests=special_requests
            )
            
            return {
                "success": True,
                "booking_reference": result.get('booking_reference'),
                "booking_details": result,
                "message": f"Booking confirmed with reference: {result.get('booking_reference')}"
            }
        except Exception as e:
            logger.error(f"Error creating booking: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to create booking"
            }
    
    async def get_booking(self, booking_reference: str) -> Dict[str, Any]:
        """
        Get booking details by reference.
        
        Args:
            booking_reference: Booking reference code
            
        Returns:
            Booking details
        """
        try:
            result = await self.api_client.get_booking(booking_reference)
            
            if result:
                formatted = format_booking_details(result)
                return {
                    "success": True,
                    "booking_details": result,
                    "formatted_details": formatted,
                    "message": "Booking found"
                }
            else:
                return {
                    "success": False,
                    "message": f"No booking found with reference: {booking_reference}"
                }
        except Exception as e:
            logger.error(f"Error getting booking: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to retrieve booking"
            }
    
    async def update_booking(
        self,
        booking_reference: str,
        date_str: Optional[str] = None,
        time_str: Optional[str] = None,
        party_size: Optional[int] = None,
        special_requests: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update an existing booking.
        
        Args:
            booking_reference: Booking reference code
            date_str: New date (optional)
            time_str: New time (optional)
            party_size: New party size (optional)
            special_requests: Updated special requests (optional)
            
        Returns:
            Update confirmation
        """
        try:
            # Parse and format date/time if provided
            formatted_date = self._parse_date(date_str) if date_str else None
            formatted_time = self._parse_time(time_str) if time_str else None
            
            # Call API
            result = await self.api_client.update_booking(
                booking_reference=booking_reference,
                visit_date=formatted_date,
                visit_time=formatted_time,
                party_size=party_size,
                special_requests=special_requests
            )
            
            return {
                "success": True,
                "booking_reference": booking_reference,
                "updates": result.get('updates', {}),
                "message": f"Booking {booking_reference} has been updated"
            }
        except Exception as e:
            logger.error(f"Error updating booking: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to update booking"
            }
    
    async def cancel_booking(
        self,
        booking_reference: str,
        reason: str = "Customer request"
    ) -> Dict[str, Any]:
        """
        Cancel a booking.
        
        Args:
            booking_reference: Booking reference code
            reason: Cancellation reason
            
        Returns:
            Cancellation confirmation
        """
        try:
            # Map reason to ID
            reason_map = {
                "customer request": 1,
                "restaurant closure": 2,
                "weather": 3,
                "emergency": 4,
                "no show": 5
            }
            reason_id = reason_map.get(reason.lower(), 1)
            
            # Call API
            result = await self.api_client.cancel_booking(
                booking_reference=booking_reference,
                cancellation_reason_id=reason_id
            )
            
            return {
                "success": True,
                "booking_reference": booking_reference,
                "message": f"Booking {booking_reference} has been cancelled"
            }
        except Exception as e:
            logger.error(f"Error cancelling booking: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to cancel booking"
            }
    
    def _parse_date(self, date_str: str) -> str:
        """
        Parse various date formats and return YYYY-MM-DD.
        
        Args:
            date_str: Date string in various formats
            
        Returns:
            Date in YYYY-MM-DD format
        """
        try:
            # Handle relative dates
            today = datetime.now().date()
            date_str_lower = date_str.lower()
            
            if 'today' in date_str_lower:
                return today.strftime('%Y-%m-%d')
            elif 'tomorrow' in date_str_lower:
                return (today + timedelta(days=1)).strftime('%Y-%m-%d')
            elif 'weekend' in date_str_lower or 'saturday' in date_str_lower:
                days_ahead = 5 - today.weekday()  # Saturday
                if days_ahead <= 0:
                    days_ahead += 7
                return (today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
            elif 'sunday' in date_str_lower:
                days_ahead = 6 - today.weekday()  # Sunday
                if days_ahead <= 0:
                    days_ahead += 7
                return (today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
            elif 'next' in date_str_lower:
                # Handle "next Friday", "next week", etc.
                if 'friday' in date_str_lower:
                    days_ahead = 4 - today.weekday()  # Friday
                    if days_ahead <= 0:
                        days_ahead += 7
                    return (today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
                elif 'week' in date_str_lower:
                    return (today + timedelta(days=7)).strftime('%Y-%m-%d')
            
            # Try to parse as absolute date
            parsed_date = parser.parse(date_str, fuzzy=True).date()
            
            # Ensure date is not in the past
            if parsed_date < today:
                # If month/day is in the past, assume next year
                if parsed_date.month < today.month or \
                   (parsed_date.month == today.month and parsed_date.day < today.day):
                    parsed_date = parsed_date.replace(year=today.year + 1)
            
            return parsed_date.strftime('%Y-%m-%d')
            
        except Exception as e:
            logger.error(f"Error parsing date '{date_str}': {str(e)}")
            # Default to tomorrow if parsing fails
            return (datetime.now().date() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    def _parse_time(self, time_str: str) -> str:
        """
        Parse various time formats and return HH:MM:SS.
        
        Args:
            time_str: Time string in various formats
            
        Returns:
            Time in HH:MM:SS format
        """
        try:
            time_str = time_str.lower().strip()
            
            # Handle common formats
            if 'pm' in time_str or 'am' in time_str:
                # Parse 12-hour format
                parsed_time = parser.parse(time_str, fuzzy=True).time()
                return parsed_time.strftime('%H:%M:%S')
            elif ':' in time_str:
                # Already in 24-hour format
                parts = time_str.split(':')
                if len(parts) == 2:
                    return f"{parts[0].zfill(2)}:{parts[1].zfill(2)}:00"
                elif len(parts) == 3:
                    return f"{parts[0].zfill(2)}:{parts[1].zfill(2)}:{parts[2].zfill(2)}"
            else:
                # Just a number (assume hours)
                hour = int(re.search(r'\d+', time_str).group())
                if hour < 12 and 'dinner' in time_str:
                    hour += 12
                return f"{hour:02d}:00:00"
            
        except Exception as e:
            logger.error(f"Error parsing time '{time_str}': {str(e)}")
            # Default to 19:00 (dinner time)
            return "19:00:00"
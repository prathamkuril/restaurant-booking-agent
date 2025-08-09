"""
Restaurant Booking API Client.

Handles all interactions with the restaurant booking API including
authentication, error handling, and response parsing.
"""

import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime, date
import logging
from urllib.parse import urlencode

logger = logging.getLogger(__name__)


class BookingAPIClient:
    """Client for interacting with the restaurant booking API."""
    
    def __init__(self, base_url: str = "http://localhost:8547"):
        """
        Initialize API client.
        
        Args:
            base_url: Base URL of the booking API
        """
        self.base_url = base_url
        self.restaurant_name = "TheHungryUnicorn"
        self.bearer_token = (
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1bmlxdWVfbmFtZSI6ImFwcGVsbGErYXBpQHJlc2RpYXJ5LmNvbSIsIm5iZiI6MTc1NDQzMDgwNSwiZXhwIjoxNzU0NTE3MjA1LCJpYXQiOjE3NTQ0MzA4MDUsImlzcyI6IlNlbGYiLCJhdWQiOiJodHRwczovL2FwaS5yZXNkaWFyeS5jb20ifQ.g3yLsufdk8Fn2094SB3J3XW-KdBc0DY9a2Jiu_56ud8"
        )
        self.headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        logger.info(f"Initialized API client with base URL: {base_url}")
    
    async def check_availability(
        self, 
        visit_date: str,
        party_size: int,
        channel_code: str = "ONLINE"
    ) -> Dict[str, Any]:
        """
        Check restaurant availability for a specific date and party size.
        
        Args:
            visit_date: Date in YYYY-MM-DD format
            party_size: Number of people
            channel_code: Booking channel (default: ONLINE)
            
        Returns:
            Availability response with available time slots
        """
        endpoint = f"/api/ConsumerApi/v1/Restaurant/{self.restaurant_name}/AvailabilitySearch"
        url = f"{self.base_url}{endpoint}"
        
        data = {
            "VisitDate": visit_date,
            "PartySize": party_size,
            "ChannelCode": channel_code
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url, 
                    headers=self.headers,
                    data=urlencode(data)
                )
                response.raise_for_status()
                result = response.json()
                logger.info(f"Successfully checked availability for {visit_date}")
                return result
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error checking availability: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error checking availability: {str(e)}")
            raise
    
    async def create_booking(
        self,
        visit_date: str,
        visit_time: str,
        party_size: int,
        channel_code: str = "ONLINE",
        special_requests: Optional[str] = None,
        customer_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new restaurant booking.
        
        Args:
            visit_date: Date in YYYY-MM-DD format
            visit_time: Time in HH:MM:SS format
            party_size: Number of people
            channel_code: Booking channel
            special_requests: Optional special requirements
            customer_info: Optional customer information
            
        Returns:
            Booking confirmation with reference
        """
        endpoint = f"/api/ConsumerApi/v1/Restaurant/{self.restaurant_name}/BookingWithStripeToken"
        url = f"{self.base_url}{endpoint}"
        
        data = {
            "VisitDate": visit_date,
            "VisitTime": visit_time,
            "PartySize": party_size,
            "ChannelCode": channel_code
        }
        
        if special_requests:
            data["SpecialRequests"] = special_requests
        
        if customer_info:
            for key, value in customer_info.items():
                if value is not None:
                    data[f"Customer[{key}]"] = value
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers=self.headers,
                    data=urlencode(data)
                )
                response.raise_for_status()
                result = response.json()
                logger.info(f"Successfully created booking: {result.get('booking_reference')}")
                return result
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error creating booking: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error creating booking: {str(e)}")
            raise
    
    async def get_booking(self, booking_reference: str) -> Dict[str, Any]:
        """
        Get booking details by reference.
        
        Args:
            booking_reference: Booking reference code
            
        Returns:
            Booking details
        """
        endpoint = f"/api/ConsumerApi/v1/Restaurant/{self.restaurant_name}/Booking/{booking_reference}"
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                result = response.json()
                logger.info(f"Successfully retrieved booking: {booking_reference}")
                return result
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Booking not found: {booking_reference}")
                return None
            logger.error(f"HTTP error getting booking: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error getting booking: {str(e)}")
            raise
    
    async def update_booking(
        self,
        booking_reference: str,
        visit_date: Optional[str] = None,
        visit_time: Optional[str] = None,
        party_size: Optional[int] = None,
        special_requests: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update an existing booking.
        
        Args:
            booking_reference: Booking reference code
            visit_date: New date (optional)
            visit_time: New time (optional)
            party_size: New party size (optional)
            special_requests: Updated special requests (optional)
            
        Returns:
            Updated booking details
        """
        endpoint = f"/api/ConsumerApi/v1/Restaurant/{self.restaurant_name}/Booking/{booking_reference}"
        url = f"{self.base_url}{endpoint}"
        
        data = {}
        if visit_date:
            data["VisitDate"] = visit_date
        if visit_time:
            data["VisitTime"] = visit_time
        if party_size:
            data["PartySize"] = party_size
        if special_requests is not None:
            data["SpecialRequests"] = special_requests
        
        if not data:
            logger.warning("No update parameters provided")
            return {"message": "No updates provided"}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    url,
                    headers=self.headers,
                    data=urlencode(data)
                )
                response.raise_for_status()
                result = response.json()
                logger.info(f"Successfully updated booking: {booking_reference}")
                return result
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error updating booking: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error updating booking: {str(e)}")
            raise
    
    async def cancel_booking(
        self,
        booking_reference: str,
        cancellation_reason_id: int = 1
    ) -> Dict[str, Any]:
        """
        Cancel a booking.
        
        Args:
            booking_reference: Booking reference code
            cancellation_reason_id: Reason ID (1-5)
            
        Returns:
            Cancellation confirmation
        """
        endpoint = f"/api/ConsumerApi/v1/Restaurant/{self.restaurant_name}/Booking/{booking_reference}/Cancel"
        url = f"{self.base_url}{endpoint}"
        
        data = {
            "micrositeName": self.restaurant_name,
            "bookingReference": booking_reference,
            "cancellationReasonId": cancellation_reason_id
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers=self.headers,
                    data=urlencode(data)
                )
                response.raise_for_status()
                result = response.json()
                logger.info(f"Successfully cancelled booking: {booking_reference}")
                return result
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error cancelling booking: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error cancelling booking: {str(e)}")
            raise
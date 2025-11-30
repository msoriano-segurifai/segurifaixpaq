"""
WebSocket Consumers for Real-time Location Tracking
"""
import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone


class LocationTrackingConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for real-time provider location tracking.

    Users connect to track their assistance request's provider location.
    Providers connect to broadcast their location.

    Connection URL patterns:
    - User tracking: /ws/tracking/request/<request_id>/
    - Provider broadcasting: /ws/tracking/provider/<provider_id>/
    """

    async def connect(self):
        """Handle WebSocket connection"""
        self.request_id = self.scope['url_route']['kwargs'].get('request_id')
        self.provider_id = self.scope['url_route']['kwargs'].get('provider_id')
        self.user = self.scope.get('user')

        # Determine room group name
        if self.request_id:
            self.room_group_name = f'tracking_request_{self.request_id}'
            self.role = 'user'
        elif self.provider_id:
            self.room_group_name = f'tracking_provider_{self.provider_id}'
            self.role = 'provider'
        else:
            await self.close()
            return

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # Send initial connection message
        await self.send_json({
            'type': 'connection_established',
            'message': 'Conectado al servicio de rastreo en tiempo real',
            'role': self.role,
            'room': self.room_group_name
        })

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive_json(self, content):
        """Handle incoming WebSocket messages"""
        message_type = content.get('type')

        if message_type == 'location_update':
            # Provider sending location update
            await self.handle_location_update(content)
        elif message_type == 'status_update':
            # Provider sending status update
            await self.handle_status_update(content)
        elif message_type == 'ping':
            # Heartbeat
            await self.send_json({'type': 'pong', 'timestamp': timezone.now().isoformat()})

    async def handle_location_update(self, content):
        """Handle location update from provider with ETA calculation"""
        latitude = content.get('latitude')
        longitude = content.get('longitude')
        heading = content.get('heading')
        speed = content.get('speed')
        accuracy = content.get('accuracy')
        request_id = content.get('request_id')

        if not latitude or not longitude:
            await self.send_json({
                'type': 'error',
                'message': 'latitude and longitude are required'
            })
            return

        # Save location and calculate ETA using tracking service
        tracking_result = await self.save_location_with_eta(
            provider_id=self.provider_id,
            latitude=latitude,
            longitude=longitude,
            heading=heading,
            speed=speed,
            accuracy=accuracy,
            request_id=request_id
        )

        # Broadcast to users tracking this provider
        location_data = {
            'type': 'location_broadcast',
            'provider_id': self.provider_id,
            'latitude': latitude,
            'longitude': longitude,
            'heading': heading,
            'speed': speed,
            'accuracy': accuracy,
            'eta': tracking_result.get('eta'),
            'distance_m': tracking_result.get('distance_m'),
            'tracking_status': tracking_result.get('tracking_status'),
            'timestamp': timezone.now().isoformat()
        }

        # Broadcast to provider's room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'location_message',
                **location_data
            }
        )

        # If request_id is provided, also broadcast to that request's room
        if request_id:
            await self.channel_layer.group_send(
                f'tracking_request_{request_id}',
                {
                    'type': 'location_message',
                    **location_data
                }
            )

    async def handle_status_update(self, content):
        """Handle status update from provider"""
        status = content.get('status')
        request_id = content.get('request_id')
        eta_minutes = content.get('eta_minutes')
        message = content.get('message', '')

        status_data = {
            'type': 'status_broadcast',
            'provider_id': self.provider_id,
            'status': status,
            'eta_minutes': eta_minutes,
            'message': message,
            'timestamp': timezone.now().isoformat()
        }

        # Broadcast to request room
        if request_id:
            await self.channel_layer.group_send(
                f'tracking_request_{request_id}',
                {
                    'type': 'status_message',
                    **status_data
                }
            )

    async def location_message(self, event):
        """Send location update to WebSocket"""
        await self.send_json({
            'type': event['type'],
            'provider_id': event.get('provider_id'),
            'latitude': event.get('latitude'),
            'longitude': event.get('longitude'),
            'heading': event.get('heading'),
            'speed': event.get('speed'),
            'accuracy': event.get('accuracy'),
            'eta': event.get('eta'),
            'distance_m': event.get('distance_m'),
            'tracking_status': event.get('tracking_status'),
            'timestamp': event.get('timestamp')
        })

    async def status_message(self, event):
        """Send status update to WebSocket"""
        await self.send_json({
            'type': event['type'],
            'provider_id': event.get('provider_id'),
            'status': event.get('status'),
            'eta_minutes': event.get('eta_minutes'),
            'message': event.get('message'),
            'timestamp': event.get('timestamp')
        })

    @database_sync_to_async
    def save_location_with_eta(self, provider_id, latitude, longitude, heading=None, speed=None, accuracy=None, request_id=None):
        """Save provider location and calculate ETA if request is active"""
        from apps.providers.models import Provider, ProviderLocation, ProviderLocationHistory
        from .models import AssistanceRequest
        from .tracking import TrackingService

        result = {'eta': None, 'distance_m': None, 'tracking_status': None}

        try:
            provider = Provider.objects.get(id=provider_id)

            # Create or update location record
            ProviderLocation.objects.update_or_create(
                provider=provider,
                defaults={
                    'latitude': latitude,
                    'longitude': longitude,
                    'heading': heading,
                    'speed': speed,
                    'accuracy': accuracy,
                    'is_online': True,
                    'last_updated': timezone.now()
                }
            )

            # If request_id provided, calculate ETA and save to history
            if request_id:
                try:
                    request = AssistanceRequest.objects.get(id=request_id)

                    # Save to location history
                    ProviderLocationHistory.objects.create(
                        provider=provider,
                        assistance_request=request,
                        latitude=latitude,
                        longitude=longitude,
                        heading=heading,
                        speed=speed
                    )

                    # Calculate ETA if user location is available
                    if request.location_latitude and request.location_longitude:
                        eta_info = TrackingService.calculate_eta(
                            latitude, longitude,
                            float(request.location_latitude),
                            float(request.location_longitude)
                        )
                        result['eta'] = eta_info
                        result['distance_m'] = eta_info.get('distance_m')

                        # Get tracking status
                        result['tracking_status'] = TrackingService.get_tracking_status(request)

                        # Auto-update arrival if very close
                        if eta_info['distance_m'] < TrackingService.ARRIVED_THRESHOLD:
                            if request.status == 'ASSIGNED' and not request.actual_arrival_time:
                                request.actual_arrival_time = timezone.now()
                                request.status = 'IN_PROGRESS'
                                request.save()
                                result['tracking_status'] = 'ARRIVED'

                except AssistanceRequest.DoesNotExist:
                    pass

        except Provider.DoesNotExist:
            pass

        return result


class AssistanceRequestConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for assistance request updates.

    Users and providers can receive real-time updates about request status,
    messages, and other events.

    Connection URL: /ws/assistance/<request_id>/
    """

    async def connect(self):
        """Handle WebSocket connection"""
        self.request_id = self.scope['url_route']['kwargs']['request_id']
        self.room_group_name = f'assistance_{self.request_id}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        await self.send_json({
            'type': 'connection_established',
            'message': 'Conectado a actualizaciones de solicitud',
            'request_id': self.request_id
        })

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive_json(self, content):
        """Handle incoming messages"""
        message_type = content.get('type')

        if message_type == 'message':
            # Chat message
            await self.handle_chat_message(content)
        elif message_type == 'ping':
            await self.send_json({'type': 'pong', 'timestamp': timezone.now().isoformat()})

    async def handle_chat_message(self, content):
        """Handle chat message between user and provider"""
        message = content.get('message')
        sender_type = content.get('sender_type')  # 'user' or 'provider'
        sender_id = content.get('sender_id')

        if not message:
            return

        # Save message to database
        await self.save_message(
            request_id=self.request_id,
            message=message,
            sender_type=sender_type,
            sender_id=sender_id
        )

        # Broadcast to room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender_type': sender_type,
                'sender_id': sender_id,
                'timestamp': timezone.now().isoformat()
            }
        )

    async def chat_message(self, event):
        """Send chat message to WebSocket"""
        await self.send_json({
            'type': 'chat_message',
            'message': event['message'],
            'sender_type': event['sender_type'],
            'sender_id': event['sender_id'],
            'timestamp': event['timestamp']
        })

    async def request_update(self, event):
        """Send request update to WebSocket"""
        await self.send_json({
            'type': 'request_update',
            'update_type': event.get('update_type'),
            'data': event.get('data'),
            'timestamp': event.get('timestamp')
        })

    async def provider_assigned(self, event):
        """Notify when provider is assigned"""
        await self.send_json({
            'type': 'provider_assigned',
            'provider': event.get('provider'),
            'eta_minutes': event.get('eta_minutes'),
            'timestamp': event.get('timestamp')
        })

    @database_sync_to_async
    def save_message(self, request_id, message, sender_type, sender_id):
        """Save chat message to database"""
        from .models import AssistanceRequest, RequestUpdate
        from apps.users.models import User

        try:
            request = AssistanceRequest.objects.get(id=request_id)
            user = User.objects.get(id=sender_id) if sender_id else request.user

            RequestUpdate.objects.create(
                request=request,
                user=user,
                update_type='MESSAGE',
                message=message,
                metadata={'sender_type': sender_type}
            )
        except (AssistanceRequest.DoesNotExist, User.DoesNotExist):
            pass

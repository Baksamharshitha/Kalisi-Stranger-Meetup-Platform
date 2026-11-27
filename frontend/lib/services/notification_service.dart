import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'api_service.dart';

// Top-level background message handler required by Firebase Messaging
@pragma('vm:entry-point')
Future<void> firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  await Firebase.initializeApp();
  if (kDebugMode) {
    print('Handling background notification: ${message.messageId} - ${message.notification?.title}');
  }
}

class NotificationService {
  NotificationService._();
  static final NotificationService instance = NotificationService._();

  static String? fcmToken;
  static final FlutterLocalNotificationsPlugin _localNotifications = FlutterLocalNotificationsPlugin();

  static const AndroidNotificationChannel _channel = AndroidNotificationChannel(
    'kalisi_high_importance_channel',
    'Kalisi Notifications',
    description: 'Notifications for dinner bookings, matches, and event updates',
    importance: Importance.high,
    playSound: true,
  );

  /// Initialize Firebase & Notification Service
  static Future<void> initialize() async {
    try {
      await Firebase.initializeApp();

      // Set background handler
      FirebaseMessaging.onBackgroundMessage(firebaseMessagingBackgroundHandler);

      // Request notification permissions
      final messaging = FirebaseMessaging.instance;
      final settings = await messaging.requestPermission(
        alert: true,
        badge: true,
        sound: true,
        provisional: false,
      );

      if (kDebugMode) {
        print('User notification permission status: ${settings.authorizationStatus}');
      }

      // Initialize Flutter Local Notifications for foreground popups
      const androidInit = AndroidInitializationSettings('@mipmap/ic_launcher');
      const initSettings = InitializationSettings(android: androidInit);

      await _localNotifications.initialize(
        initSettings,
        onDidReceiveNotificationResponse: (response) {
          if (kDebugMode) {
            print('Notification tapped: ${response.payload}');
          }
        },
      );

      // Create notification channel on Android
      await _localNotifications
          .resolvePlatformSpecificImplementation<AndroidFlutterLocalNotificationsPlugin>()
          ?.createNotificationChannel(_channel);

      // Get FCM device registration token
      try {
        fcmToken = await messaging.getToken();
        if (fcmToken != null) {
          final prefs = await SharedPreferences.getInstance();
          await prefs.setString('fcm_token', fcmToken!);
          if (kDebugMode) {
            print('==================================================================');
            print('🔥 KALISI FIREBASE FCM TOKEN:');
            print(fcmToken);
            print('==================================================================');
          }
          // Register token with Kalisi backend
          await _registerTokenWithBackend(fcmToken!);
        }
      } catch (e) {
        if (kDebugMode) print('Failed to retrieve FCM token: $e');
      }

      // Listen for token refreshes
      messaging.onTokenRefresh.listen((newToken) async {
        fcmToken = newToken;
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString('fcm_token', newToken);
        await _registerTokenWithBackend(newToken);
      });

      // Handle FOREGROUND notifications
      FirebaseMessaging.onMessage.listen((RemoteMessage message) {
        final notification = message.notification;
        final android = message.notification?.android;

        if (notification != null && android != null) {
          _localNotifications.show(
            notification.hashCode,
            notification.title ?? 'Kalisi Meetup Update',
            notification.body ?? '',
            NotificationDetails(
              android: AndroidNotificationDetails(
                _channel.id,
                _channel.name,
                channelDescription: _channel.description,
                icon: '@mipmap/ic_launcher',
                importance: Importance.high,
                priority: Priority.high,
                playSound: true,
              ),
            ),
            payload: jsonEncode(message.data),
          );
        }
      });

      // Handle notification opened app from background
      FirebaseMessaging.onMessageOpenedApp.listen((RemoteMessage message) {
        if (kDebugMode) {
          print('App opened from notification: ${message.data}');
        }
      });
    } catch (e) {
      if (kDebugMode) {
        print('NotificationService initialization error: $e');
      }
    }
  }

  /// Check if push notifications are currently authorized
  static Future<bool> isPermissionGranted() async {
    try {
      final settings = await FirebaseMessaging.instance.getNotificationSettings();
      return settings.authorizationStatus == AuthorizationStatus.authorized ||
          settings.authorizationStatus == AuthorizationStatus.provisional;
    } catch (_) {
      return false;
    }
  }

  /// Request push notification permission and register FCM device token if granted
  static Future<bool> requestPermission() async {
    try {
      final settings = await FirebaseMessaging.instance.requestPermission(
        alert: true,
        badge: true,
        sound: true,
        provisional: false,
      );
      final granted = settings.authorizationStatus == AuthorizationStatus.authorized ||
          settings.authorizationStatus == AuthorizationStatus.provisional;
      if (granted) {
        final token = await FirebaseMessaging.instance.getToken();
        if (token != null) {
          fcmToken = token;
          final prefs = await SharedPreferences.getInstance();
          await prefs.setString('fcm_token', token);
          await _registerTokenWithBackend(token);
        }
      }
      return granted;
    } catch (_) {
      return false;
    }
  }

  static Future<void> _registerTokenWithBackend(String token) async {
    try {
      await ApiService.instance.registerFcmToken(token);
    } catch (_) {}
  }
}
